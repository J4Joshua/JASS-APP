#!/usr/bin/env python3
"""Minimal MIDI → WebSocket streaming server.

MIDI piano → chord detection → JSON over WebSocket to frontend.

Run: python backend/pianomidi/ws_server.py
"""

import asyncio
import base64
import io
import json
import os
import re
import sys
import tempfile
import threading
import time
import uuid
from dataclasses import dataclass, asdict
from pathlib import Path
from fastapi import FastAPI, WebSocket, WebSocketDisconnect
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
import uvicorn
from perplexity import Perplexity
from dotenv import load_dotenv

try:
    from claude_code_sdk import query, ClaudeCodeOptions
    CLAUDE_SDK_AVAILABLE = True
except ImportError:
    CLAUDE_SDK_AVAILABLE = False

try:
    from midiutil import MIDIFile
    MIDIUTIL_AVAILABLE = True
except ImportError:
    MIDIUTIL_AVAILABLE = False

try:
    import pygame
    PYGAME_AVAILABLE = True
except ImportError:
    PYGAME_AVAILABLE = False

load_dotenv()

# Ensure backend/ is on sys.path so jass package resolves
_backend_dir = str(Path(__file__).resolve().parent.parent)
if _backend_dir not in sys.path:
    sys.path.insert(0, _backend_dir)

from jass.tis_index import TISIndex
from jass.chord_suggestion import suggest_chords
from jass.tonal_tension.weights import PAPER_WEIGHTS_TABLE1, PAPER_WEIGHTS_TABLE2
from jass.tonal_tension.theory import roman_to_chord
from constants import CURATED_SERIES

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

# --- Global state ---
clients: set[WebSocket] = set()
loop: asyncio.AbstractEventLoop | None = None
tis_idx: TISIndex | None = None
queue: asyncio.Queue[frozenset[int]] = asyncio.Queue()
spotify_client = None

# Graph tracking state
last_chroma: tuple[int, ...] | None = None
graph_depth: int = 0
nodes: list[Node] = []
relations: list[Relation] = []
allowed_suggestions: set[tuple[int, ...]] = set()
# Curated series state
series_cursor: int = 0
resolved_series: list[dict] | None = None

current_difficulty: str = "easy"
DIFFICULTY_WEIGHTS = {
    "easy": dict(PAPER_WEIGHTS_TABLE1),
    "hard": dict(PAPER_WEIGHTS_TABLE2),
}


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
    global last_chroma, graph_depth, nodes, relations, allowed_suggestions, series_cursor

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
        chroma_key = tuple(chroma)
        names = [NOTE_NAMES[pc] for pc in sorted(pitch_classes)]

        chord_name: str | None = None
        if len(names) >= 2:
            chords = find_chords_from_notes(names)
            if chords:
                chord_name = str(chords[0])
        if chord_name is None:
            chord_name = "-".join(names) if names else "?"

        print(f"[chord_worker] detected: {chord_name!r}  notes: {names}  chroma={list(chroma_key)}", file=sys.stderr)

        # Gate: if we have suggestions, only accept chords whose chroma matches
        if allowed_suggestions and chroma_key not in allowed_suggestions:
            print(f"[chord_worker] REJECTED {chord_name!r}  played={list(chroma_key)}  allowed={[list(c) for c in allowed_suggestions]}", file=sys.stderr)
            continue

        print(f"[chord_worker] ACCEPTED {chord_name!r}  chroma={list(chroma_key)}", file=sys.stderr)

        # Advance curated series cursor if the played chord matches
        if resolved_series and list(chroma_key) == resolved_series[series_cursor]["chroma"]:
            print(f"[chord_worker] series match: {resolved_series[series_cursor]['name']}, advancing cursor", file=sys.stderr)
            series_cursor = (series_cursor + 1) % len(resolved_series)

        # Get suggestions for accepted chord
        weights = DIFFICULTY_WEIGHTS[current_difficulty]
        print(f"[chord_worker] difficulty={current_difficulty}", file=sys.stderr)
        suggestions = await asyncio.to_thread(
            _get_suggestions, weights, chord_name, chroma
        )

        print(f"[chord_worker] suggestions: {[s['name'] for s in suggestions]}", file=sys.stderr)

        # Update allowed suggestions for next chord (set of chroma tuples)
        allowed_suggestions = {tuple(s["chroma"]) for s in suggestions}

        # Check if chord changed (by chroma) and update graph
        if chroma_key != last_chroma:
            last_chroma = chroma_key
            graph_depth += 1

            # Create node for current chord
            current_node = Node(
                uuid=str(uuid.uuid4()),
                name=chord_name,
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
            "chord": {"name": chord_name, "notes": names, "chroma": chroma},
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

def _get_suggestions(weights: dict[str, float], chord_name: str, chroma: list[int] | None = None) -> list[dict]:
    if tis_idx is None:
        return []

    # Two TIS-based goals (resolve + tension), then the curated series chord
    goals = ["resolve", "tension"]

    out: list[dict] = []
    try:
        for goal in goals:
            result = suggest_chords(
                weights=weights,
                chroma=chroma,
                key="C",
                index=tis_idx,
                top=1,          # top 1 per goal
                goal=goal,      # different goal each call
            )

            # Ensure we always append *one* item per goal
            rlist = result.get("results", []) or []
            if not rlist:
                out.append({
                    "name": None,
                    "notes": [],
                    "chroma": [],
                    "tension": 0.0,
                    "goal": goal,
                })
                continue

            r = rlist[0]
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
                "goal": goal,
            })

        # Append curated series chord as the 3rd suggestion
        if resolved_series:
            entry = resolved_series[series_cursor]
            out.append({
                "name": entry["name"],
                "notes": list(entry["notes"]),
                "chroma": list(entry["chroma"]),
                "tension": 0.0,
                "goal": "series",
            })
        else:
            out.append({
                "name": None,
                "notes": [],
                "chroma": [],
                "tension": 0.0,
                "goal": "series",
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
    global last_chroma, graph_depth, nodes, relations, allowed_suggestions, current_difficulty, series_cursor
    current_difficulty = "easy"
    last_chroma = None
    graph_depth = 0
    nodes = []
    relations = []
    allowed_suggestions = set()
    series_cursor = 0
    print(f"[ws] Session reset", file=sys.stderr)


@app.get("/status")
async def get_status():
    """Check the status of the backend and available services."""
    return {
        "status": "online",
        "services": {
            "tis_index": "available" if tis_idx is not None else "unavailable",
            "spotify": "available" if spotify_client is not None else "unavailable",
            "midi": "disabled" if os.environ.get("DISABLE_MIDI") in ("1", "true") else "enabled",
        }
    }


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

@app.get("/recommend-songs/{filename}")
async def recommend_songs(filename: str):
    """
    Get song recommendations based on the last 5 played chords
    from a session using the Perplexity API.
    """
    try:
        # Load session
        session_file = Path(__file__).resolve().parent / "sessions" / filename
        
        # Security: only allow session_*.json files
        if not filename.startswith("session_") or not filename.endswith(".json"):
            return {"error": "Invalid filename"}
        
        if not session_file.exists():
            return {"error": "Session not found"}
        
        with open(session_file, "r") as f:
            session_data = json.load(f)
        
        # Extract played chords (nodes that have outgoing edges)
        nodes = session_data.get("nodes", [])
        relations = session_data.get("relations", [])
        
        source_node_ids = {rel["source_node"] for rel in relations}
        played_nodes = [n for n in nodes if n["uuid"] in source_node_ids]
        
        # Sort by depth to get the progression order
        played_nodes.sort(key=lambda n: n["depth"])
        
        # Get the last 5 played chords
        last_5_chords = played_nodes[-5:]
        chord_names = [n["name"] for n in last_5_chords]
        chord_progression = " -> ".join(chord_names)
        
        print(f"[recommend_songs] Chord progression: {chord_progression}", file=sys.stderr)
        
        # Call Perplexity API
        # from perplexityai import Perplexity

        client = Perplexity(api_key=os.environ.get("PERPLEXITY_API_KEY"))

        prompt = (
            "Return EXACTLY 5 lines. Each line must be in the format: "
            "Song Title - Artist Name. Do not include numbering, bullets, quotes, "
            "citations, commentary, or extra text.\n"
            f"Chord progression: {chord_progression}"
        )
        
        completion = client.chat.completions.create(
            model="sonar-pro",
            messages=[
                {"role": "user", "content": prompt}
            ]
        )
        
        response_text = completion.choices[0].message.content
        
        # Parse the response into a list of songs
        # Expected format: "Song Title - Artist Name"
        song_titles = []
        lines = response_text.split("\n")

        for raw_line in lines:
            line = raw_line.strip()
            if not line:
                continue
            line = line.replace("**", "").strip()
            # Remove leading numbering or bullets if present
            line = line.lstrip("0123456789.-) ").strip()
            if " - " in line and len(line) > 5:
                song_titles.append(line)

        # Retry once with a stricter prompt if formatting is off
        if len(song_titles) < 5:
            retry_prompt = (
                "Output ONLY 5 lines. Each line: Song Title - Artist Name. "
                "No other text. No bullets. No numbering.\n"
                f"Chord progression: {chord_progression}"
            )
            retry = client.chat.completions.create(
                model="sonar-pro",
                messages=[{"role": "user", "content": retry_prompt}],
            )
            retry_text = retry.choices[0].message.content
            retry_lines = retry_text.split("\n")
            song_titles = []
            for raw_line in retry_lines:
                line = raw_line.strip()
                if not line:
                    continue
                line = line.replace("**", "").strip()
                line = line.lstrip("0123456789.-) ").strip()
                if " - " in line and len(line) > 5:
                    song_titles.append(line)

        # Limit to 5 songs
        song_titles = song_titles[:5]

        print(f"[recommend_songs] Parsed {len(song_titles)} songs from Perplexity: {song_titles}", file=sys.stderr)
        
        # Enrich with Spotify data
        enriched_songs = []
        if spotify_client:
            print(f"[recommend_songs] Spotify client available, searching for {len(song_titles)} songs", file=sys.stderr)
            for song_title in song_titles:
                try:
                    print(f"[recommend_songs] Searching Spotify for: {song_title}", file=sys.stderr)
                    # Search Spotify for the song
                    results = await asyncio.to_thread(
                        spotify_client.search, q=song_title, type="track", limit=1
                    )
                    
                    if results and results.get("tracks", {}).get("items"):
                        track = results["tracks"]["items"][0]
                        print(f"[recommend_songs] Found: {track.get('name')} by {', '.join([a['name'] for a in track.get('artists', [])])}", file=sys.stderr)
                        
                        # Extract relevant data
                        album_art = None
                        if track.get("album", {}).get("images"):
                            # Get the largest image
                            images = track["album"]["images"]
                            album_art = images[0]["url"] if images else None
                        
                        artists_names = ", ".join([artist["name"] for artist in track.get("artists", [])])
                        spotify_url = track.get("external_urls", {}).get("spotify")
                        
                        enriched_songs.append({
                            "title": track["name"],
                            "artists": artists_names,
                            "album": track.get("album", {}).get("name", ""),
                            "image_url": album_art,
                            "spotify_url": spotify_url,
                            "original_query": song_title,
                        })
                    else:
                        print(f"[recommend_songs] Not found on Spotify: {song_title}", file=sys.stderr)
                        # Fallback if not found on Spotify
                        enriched_songs.append({
                            "title": song_title,
                            "artists": "",
                            "album": "",
                            "image_url": None,
                            "spotify_url": None,
                            "original_query": song_title,
                        })
                except Exception as e:
                    print(f"[recommend_songs] Error searching Spotify for '{song_title}': {e}", file=sys.stderr)
                    enriched_songs.append({
                        "title": song_title,
                        "artists": "",
                        "album": "",
                        "image_url": None,
                        "spotify_url": None,
                        "original_query": song_title,
                    })
        else:
            print(f"[recommend_songs] Spotify client not available", file=sys.stderr)
            # No Spotify client, return basic info
            enriched_songs = [
                {
                    "title": song_title,
                    "artists": "",
                    "album": "",
                    "image_url": None,
                    "spotify_url": None,
                    "original_query": song_title,
                }
                for song_title in song_titles
            ]
        
        print(f"[recommend_songs] Enriched {len(enriched_songs)} songs with Spotify data", file=sys.stderr)
        
        return {
            "status": "success",
            "chord_progression": chord_progression,
            "songs": enriched_songs,
        }
    except Exception as e:
        print(f"[recommend_songs] Error: {e}", file=sys.stderr)
        import traceback
        traceback.print_exc(file=sys.stderr)
        return {"error": str(e), "status": "failed"}


# --- Create Song (Claude SDK + MIDI generation) ---

class CreateSongRequest(BaseModel):
    chords: list[str]


def play_midi_background(midi_bytes: bytes) -> None:
    """Write MIDI bytes to a temp file, play via pygame, then clean up."""
    tmp = tempfile.NamedTemporaryFile(suffix=".mid", delete=False)
    try:
        tmp.write(midi_bytes)
        tmp.close()
        pygame.mixer.music.load(tmp.name)
        pygame.mixer.music.play()
        while pygame.mixer.music.get_busy():
            time.sleep(0.1)
    except Exception as e:
        print(f"[play_midi] Error: {e}", file=sys.stderr)
    finally:
        try:
            os.unlink(tmp.name)
        except OSError:
            pass


def generate_midi_from_bars(bars: list) -> bytes:
    """Convert structured bar data (from Claude) into a MIDI file returned as bytes."""
    midi = MIDIFile(3)  # 3 tracks: melody, chords, bass
    tempo = 120
    for track in range(3):
        midi.addTempo(track, 0, tempo)
    midi.addTrackName(0, 0, "Melody")
    midi.addTrackName(1, 0, "Chords")
    midi.addTrackName(2, 0, "Bass")

    for bar_idx, bar in enumerate(bars):
        bar_start = bar_idx * 4  # 4 beats per bar

        # Chord voicing – whole notes
        for note in bar.get("chord_notes", []):
            midi.addNote(1, 0, int(note), bar_start, 4, 80)

        # Bass note – whole note
        bass = bar.get("bass_note")
        if bass is not None:
            midi.addNote(2, 0, int(bass), bar_start, 4, 90)

        # Melody notes
        for mn in bar.get("melody_notes", []):
            midi.addNote(
                0, 0,
                int(mn["pitch"]),
                bar_start + float(mn["start"]),
                float(mn["duration"]),
                100,
            )

    buf = io.BytesIO()
    midi.writeFile(buf)
    return buf.getvalue()


@app.post("/generate-track")
async def create_song(req: CreateSongRequest):
    """Generate an 8-bar jazz MIDI file from a list of chords using the Claude Code SDK."""
    if not CLAUDE_SDK_AVAILABLE:
        return {"error": "claude-code-sdk is not installed", "status": "failed"}
    if not MIDIUTIL_AVAILABLE:
        return {"error": "midiutil is not installed", "status": "failed"}

    chords = req.chords
    if not chords:
        return {"error": "No chords provided", "status": "failed"}

    chord_list = ", ".join(chords)
    prompt = (
        f"You are a world-class bebop jazz player in the style of Chad Baker. "
        f"Given these chords from a session: {chord_list}\n\n"
        "Create an 8-bar jazz arrangement that SWINGS HARD. Cycle through the provided chords to fill 8 bars.\n"
        "Return ONLY valid JSON (no markdown fences, no explanation, no extra text) with this exact structure:\n"
        "{\n"
        '  "abc_notation": "X:1\\nT:Jazz Session\\nM:4/4\\nL:1/8\\nK:C\\n...",\n'
        '  "bars": [\n'
        "    {\n"
        '      "chord_name": "Dm7",\n'
        '      "chord_notes": [62, 65, 69, 72],\n'
        '      "bass_note": 38,\n'
        '      "melody_notes": [\n'
        '        {"pitch": 74, "start": 0.0, "duration": 1.0},\n'
        '        {"pitch": 72, "start": 1.0, "duration": 0.5}\n'
        "      ]\n"
        "    }\n"
        "  ]\n"
        "}\n\n"
        "Rules:\n"
        "- MIDI note numbers: 60 = middle C (C4)\n"
        "- chord_notes: use rich jazz voicings — drop-2, rootless, shell voicings with 7ths, 9ths, 13ths. Range 55-72. "
        "Avoid plain triads; every chord should have at least a 7th.\n"
        "- bass_note: walking bass line, not just roots — use approach tones, chromatic passing notes, and 5ths. Range 36-48.\n"
        "- melody_notes: 4-8 notes per bar. Use swing 8th-note feel (long-short pairs), bebop scales, "
        "chromatic enclosures, approach patterns, and blue notes (b3, b5, b7). Mix syncopation with on-beat accents. "
        "Include occasional triplet rhythms (duration 0.33). Range 60-84.\n"
        "- Vary rhythmic density: some bars dense and busy, others spacious with longer tones\n"
        "- Use voice leading between bars — melody notes should connect smoothly\n"
        "- abc_notation: complete ABC notation of the melody line\n"
    )

    try:
        print(f"[create_song] Calling Claude SDK with chords: {chord_list}", file=sys.stderr)
        response_text = ""
        async for message in query(
            prompt=prompt,
            options=ClaudeCodeOptions(max_turns=1),
        ):
            if hasattr(message, "content"):
                for block in message.content:
                    if hasattr(block, "text"):
                        response_text += block.text

        print(f"[create_song] Raw response length: {len(response_text)}", file=sys.stderr)

        # Extract JSON from response (Claude may wrap it in text)
        json_match = re.search(r"\{[\s\S]*\}", response_text)
        if not json_match:
            return {"error": "Could not parse JSON from Claude response", "status": "failed"}

        data = json.loads(json_match.group())
        bars = data.get("bars", [])
        abc_notation = data.get("abc_notation", "")

        if not bars:
            return {"error": "Claude returned no bars", "status": "failed"}

        # Generate MIDI
        midi_bytes = generate_midi_from_bars(bars)
        midi_b64 = base64.b64encode(midi_bytes).decode()

        print(f"[create_song] Generated MIDI: {len(midi_bytes)} bytes, {len(bars)} bars", file=sys.stderr)

        # Auto-play MIDI in background thread
        if PYGAME_AVAILABLE:
            asyncio.create_task(asyncio.to_thread(play_midi_background, midi_bytes))

        return {
            "status": "success",
            "abc_notation": abc_notation,
            "midi_base64": midi_b64,
            "bars": bars,
        }
    except Exception as e:
        print(f"[create_song] Error: {e}", file=sys.stderr)
        import traceback
        traceback.print_exc(file=sys.stderr)
        return {"error": str(e), "status": "failed"}


@app.websocket("/ws")
async def ws_endpoint(ws: WebSocket):
    global current_difficulty
    await ws.accept()
    clients.add(ws)
    try:
        while True:
            raw = await ws.receive_text()
            try:
                msg = json.loads(raw)
                if msg.get("type") == "set_difficulty":
                    difficulty = msg.get("difficulty", "easy")
                    if difficulty in DIFFICULTY_WEIGHTS:
                        current_difficulty = difficulty
                        print(f"[ws] Difficulty set to: {difficulty}", file=sys.stderr)
            except (json.JSONDecodeError, AttributeError):
                pass
    except WebSocketDisconnect:
        clients.discard(ws)


# --- Lifecycle ---

def _resolve_curated_series(idx: TISIndex) -> None:
    """Resolve the first CURATED_SERIES into concrete {name, notes, chroma} dicts."""
    global resolved_series
    _name, numerals = CURATED_SERIES[0]
    name_to_row = idx.build_name_to_row()
    result: list[dict] = []
    for numeral in numerals:
        chord_name = roman_to_chord(numeral, "C")
        # Normalize: the index may store "Bm7b5" instead of "Bø7"
        lookup_name = chord_name.replace("ø", "m7b5")
        row = name_to_row.get(chord_name) or name_to_row.get(lookup_name)
        if row is None:
            print(f"[ws] series: could not find {chord_name!r} (or {lookup_name!r}) in index, skipping", file=sys.stderr)
            continue
        bits = idx.chroma_bits[row].tolist()
        notes = [NOTE_NAMES[i] for i, b in enumerate(bits) if b]
        result.append({"name": chord_name, "notes": notes, "chroma": bits})
    resolved_series = result
    print(f"[ws] Curated series resolved: {[c['name'] for c in result]}", file=sys.stderr)


@app.on_event("startup")
async def startup():
    global loop, tis_idx, spotify_client

    loop = asyncio.get_running_loop()

    # load chord suggestion index
    try:
        idx_path = Path(__file__).resolve().parent / "jass" / "tis_index.npz"
        tis_idx = TISIndex.from_npz(idx_path)
        print(f"[ws] TIS index loaded", file=sys.stderr)
    except Exception as e:
        print(f"[ws] TIS index unavailable: {e}", file=sys.stderr)

    # Resolve curated series into concrete chord dicts
    if tis_idx is not None and CURATED_SERIES:
        _resolve_curated_series(tis_idx)
    # Initialize Spotify client
    try:
        import spotipy
        from spotipy.oauth2 import SpotifyClientCredentials
        
        client_id = os.environ.get("SPOTIFY_CLIENT_ID")
        client_secret = os.environ.get("SPOTIFY_CLIENT_SECRET")
        
        if client_id and client_secret:
            auth_manager = SpotifyClientCredentials(client_id=client_id, client_secret=client_secret)
            spotify_client = spotipy.Spotify(auth_manager=auth_manager)
            print(f"[ws] Spotify client initialized", file=sys.stderr)
        else:
            print(f"[ws] Spotify credentials not found (SPOTIFY_CLIENT_ID, SPOTIFY_CLIENT_SECRET)", file=sys.stderr)
    except Exception as e:
        print(f"[ws] Spotify client init failed: {e}", file=sys.stderr)

    # Initialize pygame mixer for MIDI playback
    if PYGAME_AVAILABLE:
        try:
            pygame.mixer.init()
            print("[ws] pygame mixer initialized", file=sys.stderr)
        except Exception as e:
            print(f"[ws] pygame mixer init failed: {e}", file=sys.stderr)

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
