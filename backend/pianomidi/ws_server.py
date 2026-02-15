#!/usr/bin/env python3
"""Minimal MIDI → WebSocket streaming server.

MIDI piano → chord detection → JSON over WebSocket to frontend.

Run: python backend/pianomidi/ws_server.py
"""

import asyncio
import json
import os
import sys
import threading
from pathlib import Path

from fastapi import FastAPI, WebSocket, WebSocketDisconnect
import uvicorn

# Ensure backend/ is on sys.path so jass package resolves
_backend_dir = str(Path(__file__).resolve().parent.parent)
if _backend_dir not in sys.path:
    sys.path.insert(0, _backend_dir)

from jass.tis_index import TISIndex
from jass.chord_suggestion import suggest_chords

app = FastAPI()

NOTE_NAMES = ["C", "C#", "D", "D#", "E", "F", "F#", "G", "G#", "A", "A#", "B"]

# --- Global state ---
clients: set[WebSocket] = set()
loop: asyncio.AbstractEventLoop | None = None
tis_idx: TISIndex | None = None
queue: asyncio.Queue[frozenset[int]] = asyncio.Queue()


# --- Stage 1: MIDI capture (rtmidi thread) ---

class MidiCapture:
    """Captures MIDI note-on/off, debounces, and pushes snapshots to an asyncio queue."""

    def __init__(self, q: asyncio.Queue, event_loop: asyncio.AbstractEventLoop):
        self.held: set[int] = set()
        self.q = q
        self.loop = event_loop
        self._timer: threading.Timer | None = None
        self._lock = threading.Lock()

    def callback(self, event, _data=None):
        message, _ = event
        status = message[0] & 0xF0
        note = message[1]
        velocity = message[2] if len(message) > 2 else 0

        if status == 0x90 and velocity > 0:
            self.held.add(note)
        elif status == 0x80 or (status == 0x90 and velocity == 0):
            self.held.discard(note)
        else:
            return

        self._debounce()

    def _debounce(self, delay: float = 0.03):
        with self._lock:
            if self._timer:
                self._timer.cancel()
            self._timer = threading.Timer(delay, self._emit)
            self._timer.daemon = True
            self._timer.start()

    def _emit(self):
        snapshot = frozenset(self.held)
        self.loop.call_soon_threadsafe(self.q.put_nowait, snapshot)


# --- Stage 2: chord detection + suggestion worker (async) ---

async def chord_worker():
    """Reads note snapshots from the queue, detects chords, broadcasts."""
    from pychord.analyzer import find_chords_from_notes

    while True:
        snapshot = await queue.get()

        # drain to latest — skip stale intermediate states
        while not queue.empty():
            snapshot = queue.get_nowait()

        # build chroma + note names
        pitch_classes = {n % 12 for n in snapshot}
        chroma = [1 if i in pitch_classes else 0 for i in range(12)]
        names = [NOTE_NAMES[pc] for pc in sorted(pitch_classes)]

        # detect chord
        chord_name = None
        if len(names) >= 2:
            chords = find_chords_from_notes(names)
            if chords:
                chord_name = str(chords[0])

        # compute suggestions (offload to thread so we don't block the loop)
        suggestions = await asyncio.to_thread(_get_suggestions, chord_name, chroma)

        await broadcast({
            "type": "chord",
            "chord": {"name": chord_name, "notes": names, "chroma": chroma},
            "suggestions": suggestions,
        })


def _get_suggestions(chord_name: str | None, chroma: list[int]) -> list[dict]:
    if tis_idx is None or (not chord_name and not any(chroma)):
        return []
    try:
        result = suggest_chords(chord=chord_name, chroma=chroma, key="C", index=tis_idx, top=3, goal="resolve")
        out = []
        for r in result.get("results", []):
            row = int(r["row"])
            bits = tis_idx.chroma_bits[row].tolist()
            notes = [n.capitalize() for n in r.get("notes", [])]
            if not notes:
                notes = [NOTE_NAMES[i] for i, b in enumerate(bits) if b]
            out.append({
                "name": r["name"],
                "notes": notes,
                "chroma": bits,
                "tension": round(float(r.get("tension", 0)), 3),
            })
        return out
    except Exception as e:
        print(f"[ws] suggest error: {e}", file=sys.stderr)
        return []


# --- Stage 3: WebSocket broadcast ---

async def broadcast(message: dict):
    if not clients:
        return
    text = json.dumps(message)
    results = await asyncio.gather(
        *[ws.send_text(text) for ws in clients],
        return_exceptions=True,
    )
    for ws, result in zip(list(clients), results):
        if isinstance(result, Exception):
            clients.discard(ws)


@app.websocket("/ws")
async def ws_endpoint(ws: WebSocket):
    await ws.accept()
    clients.add(ws)
    try:
        while True:
            await ws.receive_text()
    except WebSocketDisconnect:
        clients.discard(ws)


# --- Lifecycle ---

@app.on_event("startup")
async def startup():
    global loop, tis_idx

    loop = asyncio.get_running_loop()

    # load chord suggestion index
    try:
        idx_path = Path(__file__).resolve().parent.parent / "jass" / "tis_index.npz"
        tis_idx = TISIndex.from_npz(idx_path)
        print(f"[ws] TIS index loaded", file=sys.stderr)
    except Exception as e:
        print(f"[ws] TIS index unavailable: {e}", file=sys.stderr)

    # start the chord detection worker
    asyncio.create_task(chord_worker())

    # init MIDI
    if os.environ.get("DISABLE_MIDI") in ("1", "true"):
        print("[ws] MIDI disabled", file=sys.stderr)
        return

    try:
        import rtmidi
        midi_in = rtmidi.MidiIn()
        ports = midi_in.get_ports()
        if not ports:
            print("[ws] No MIDI ports found", file=sys.stderr)
            return

        capture = MidiCapture(queue, loop)
        midi_in.set_callback(capture.callback)
        midi_in.open_port(0)
        # prevent GC
        app.state.midi_in = midi_in
        print(f"[ws] MIDI: {ports[0]}", file=sys.stderr)
    except Exception as e:
        print(f"[ws] MIDI init failed: {e}", file=sys.stderr)


@app.on_event("shutdown")
async def shutdown():
    clients.clear()


if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8000)
