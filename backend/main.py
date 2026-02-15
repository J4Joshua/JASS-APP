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
import uuid
from dataclasses import dataclass, asdict
from pathlib import Path

from fastapi import FastAPI, WebSocket, WebSocketDisconnect
from fastapi.middleware.cors import CORSMiddleware
import uvicorn

# Ensure backend/ is on sys.path so jass package resolves
_backend_dir = str(Path(__file__).resolve().parent.parent)
if _backend_dir not in sys.path:
    sys.path.insert(0, _backend_dir)

from jass.tis_index import TISIndex
from jass.chord_suggestion import suggest_chords

app = FastAPI()

# --- CORS Configuration ---
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Allow all origins for development
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# --- Graph Data Structures ---

@dataclass
class Node:
    """Represents a chord node in the graph."""
    uuid: str
    name: str
    depth: int
    chroma: list[int]

@dataclass
class Relation:
    """Represents a directed edge from one chord to another."""
    uuid: str
    source_node: str
    target_node: str

NOTE_NAMES = ["C", "C#", "D", "D#", "E", "F", "F#", "G", "G#", "A", "A#", "B"]

# Custom note-set → chord name overrides (checked before pychord)
CHORD_OVERRIDES: dict[frozenset[str], str] = {
    frozenset({"C", "D", "F"}): "F5/D",
}

# --- Global state ---
clients: set[WebSocket] = set()
loop: asyncio.AbstractEventLoop | None = None
tis_idx: TISIndex | None = None
queue: asyncio.Queue[frozenset[int]] = asyncio.Queue()

# Graph tracking state
last_chord_name: str | None = None
graph_depth: int = 0
nodes: list[Node] = []
relations: list[Relation] = []
allowed_suggestions: set[str] = set()


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
    global last_chord_name, graph_depth, nodes, relations, allowed_suggestions

    from pychord.analyzer import find_chords_from_notes

    while True:
      try:
        snapshot = await queue.get()

        # drain to latest — skip stale intermediate states
        while not queue.empty():
            snapshot = queue.get_nowait()

        # build chroma + note names
        pitch_classes = {n % 12 for n in snapshot}
        chroma = [1 if i in pitch_classes else 0 for i in range(12)]
        names = [NOTE_NAMES[pc] for pc in sorted(pitch_classes)]

        # detect chord (check overrides first, then pychord)
        chord_name = CHORD_OVERRIDES.get(frozenset(names))
        if chord_name is None and len(names) >= 2:
            chords = find_chords_from_notes(names)
            if chords:
                chord_name = str(chords[0])

        print(f"[chord_worker] detected: {chord_name!r}  notes: {names}", file=sys.stderr)

        # Gate: ignore unrecognized input
        if chord_name is None:
            print(f"[chord_worker] skipped: no chord recognized", file=sys.stderr)
            continue

        # Gate: if we have suggestions, only accept matching chords
        root_name = chord_name.split("/")[0]
        if allowed_suggestions and root_name not in allowed_suggestions:
            print(f"[chord_worker] REJECTED {chord_name!r} (root={root_name!r}) — not in allowed {allowed_suggestions}", file=sys.stderr)
            continue

        print(f"[chord_worker] ACCEPTED {chord_name!r} (root={root_name!r})", file=sys.stderr)

        # Get suggestions for accepted chord (use root name for lookup)
        suggestions = await asyncio.to_thread(
            _get_suggestions, root_name, None
        )

        print(f"[chord_worker] suggestions: {[s['name'] for s in suggestions]}", file=sys.stderr)

        # Update allowed suggestions for next chord
        allowed_suggestions = {s["name"] for s in suggestions}
        print(f"[chord_worker] allowed_suggestions now: {allowed_suggestions}", file=sys.stderr)

        # Check if chord changed and update graph
        if root_name != last_chord_name:
            last_chord_name = root_name
            graph_depth += 1

            # Create node for current chord
            current_node = Node(
                uuid=str(uuid.uuid4()),
                name=root_name,
                depth=graph_depth,
                chroma=chroma
            )
            nodes.append(current_node)

            # Create nodes for suggestions and relations
            for sugg in suggestions:
                sugg_node = Node(
                    uuid=str(uuid.uuid4()),
                    name=sugg["name"],
                    depth=graph_depth + 1,
                    chroma=sugg["chroma"]
                )
                nodes.append(sugg_node)

                # Create relation from current to suggestion
                relation = Relation(
                    uuid=str(uuid.uuid4()),
                    source_node=current_node.uuid,
                    target_node=sugg_node.uuid
                )
                relations.append(relation)

        await broadcast({
            "type": "chord",
            "chord": {"name": root_name, "notes": names, "chroma": chroma},
            "suggestions": suggestions,
            "graph": {
                "nodes": [asdict(n) for n in nodes],
                "relations": [asdict(r) for r in relations],
            },
        })
      except Exception as e:
        import traceback
        print(f"[chord_worker] ERROR: {e}", file=sys.stderr)
        traceback.print_exc(file=sys.stderr)


def _get_suggestions(chord_name: str, chroma: list[int] | None = None) -> list[dict]:
    if tis_idx is None:
        return []
    try:
        result = suggest_chords(chord=chord_name, key="C", index=tis_idx, top=3, goal="resolve")
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
        print(f"[ws] suggest error: chord={chord_name!r} chroma={chroma} → {e}", file=sys.stderr)
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


# --- Session Management ---

def save_session() -> dict:
    """Save current session to a JSON file and return the session data."""
    from datetime import datetime
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    
    session_data = {
        "timestamp": timestamp,
        "nodes": [asdict(n) for n in nodes],
        "relations": [asdict(r) for r in relations],
        "total_depth": graph_depth,
    }
    
    # Create sessions directory if it doesn't exist
    sessions_dir = Path(__file__).resolve().parent / "sessions"
    sessions_dir.mkdir(exist_ok=True)
    
    # Save to file with timestamp
    session_file = sessions_dir / f"session_{timestamp}.json"
    
    with open(session_file, "w") as f:
        json.dump(session_data, f, indent=2)
    
    print(f"[ws] Session saved to {session_file}", file=sys.stderr)
    return session_data

def reset_session():
    """Reset global state for a new session."""
    global last_chord_name, graph_depth, nodes, relations, allowed_suggestions
    last_chord_name = None
    graph_depth = 0
    nodes = []
    relations = []
    allowed_suggestions = set()
    print(f"[ws] Session reset", file=sys.stderr)


@app.get("/sessions")
async def list_sessions():
    """List all available session files."""
    sessions_dir = Path(__file__).resolve().parent / "sessions"
    if not sessions_dir.exists():
        return {"sessions": []}
    
    sessions = []
    for session_file in sorted(sessions_dir.glob("session_*.json"), reverse=True):
        try:
            with open(session_file, "r") as f:
                data = json.load(f)
            sessions.append({
                "filename": session_file.name,
                "timestamp": data.get("timestamp"),
                "total_depth": data.get("total_depth", 0),
                "node_count": len(data.get("nodes", [])),
            })
        except Exception as e:
            print(f"[ws] Error reading session {session_file}: {e}", file=sys.stderr)
    
    return {"sessions": sessions}

@app.get("/sessions/{filename}")
async def get_session(filename: str):
    """Load a specific session file."""
    session_file = Path(__file__).resolve().parent / "sessions" / filename
    
    # Security: only allow session_*.json files
    if not filename.startswith("session_") or not filename.endswith(".json"):
        return {"error": "Invalid filename"}
    
    if not session_file.exists():
        return {"error": "Session not found"}
    
    try:
        with open(session_file, "r") as f:
            data = json.load(f)
        return data
    except Exception as e:
        print(f"[ws] Error reading session {filename}: {e}", file=sys.stderr)
        return {"error": "Failed to read session"}

@app.post("/end-session")
async def end_session():
    """End the current session, save it, and reset state."""
    session_data = save_session()
    reset_session()
    return {
        "status": "session_ended",
        "message": "Session saved and reset",
        "session": session_data,
    }

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
        idx_path = Path(__file__).resolve().parent / "jass" / "tis_index.npz"
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
