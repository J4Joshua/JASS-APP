"""
Modal deployment for JASS multi-turn chord coaching.

Run locally: modal serve modal_app.py
Deploy: modal deploy modal_app.py
"""
import modal
import json
from datetime import datetime, timedelta
from pathlib import Path

# Create Modal app
app = modal.App("jass-chord-coach")

# Build image with dependencies
image = (
    modal.Image.debian_slim()
    .pip_install(
        "numpy",
        "scipy", 
        "perplexityai",
        "spotipy",
        "pychord",
    )
)

# Mount your jass package and index files
jass_mount = modal.Mount.from_local_dir(
    Path(__file__).parent / "jass",
    remote_path="/root/jass"
)

# ==================== STATE MANAGEMENT ====================

# Option 1: In-memory (good for hackathon/demo)
# Persists as long as container is warm (~10 min after last use)
session_state = {}

class SessionState:
    """Manages multi-turn conversation state."""
    
    def __init__(self, session_id: str):
        self.session_id = session_id
        self.history = []  # List of {chord, suggestions, exercise, timestamp}
        self.difficulty = 1  # Current difficulty level
        self.patterns_detected = []  # E.g., ["ii-V", "tritone-sub"]
        self.created_at = datetime.utcnow()
        self.last_updated = datetime.utcnow()
    
    def add_turn(self, chord: str, suggestions: list, exercise: str):
        """Record a turn in the conversation."""
        turn = {
            "chord": chord,
            "suggestions": suggestions,
            "exercise": exercise,
            "timestamp": datetime.utcnow().isoformat(),
        }
        self.history.append(turn)
        self.last_updated = datetime.utcnow()
    
    def detect_pattern(self, chord: str) -> str | None:
        """Detect if user followed a progression pattern."""
        if len(self.history) < 1:
            return None
        
        last_chord = self.history[-1]["chord"]
        
        # Basic pattern detection (extend with your TIS logic)
        if "m7" in last_chord and "7" in chord and not "m7" in chord:
            return "ii-V progression"
        
        # Tritone substitution detection
        if "7" in last_chord and "b7" in chord:
            return "tritone substitution"
        
        return None
    
    def to_dict(self) -> dict:
        return {
            "session_id": self.session_id,
            "history": self.history,
            "difficulty": self.difficulty,
            "patterns_detected": self.patterns_detected,
            "created_at": self.created_at.isoformat(),
            "last_updated": self.last_updated.isoformat(),
        }

def get_or_create_session(session_id: str) -> SessionState:
    """Get existing session or create new one."""
    if session_id not in session_state:
        session_state[session_id] = SessionState(session_id)
    return session_state[session_id]

def cleanup_old_sessions():
    """Remove sessions older than 1 hour."""
    cutoff = datetime.utcnow() - timedelta(hours=1)
    to_remove = [
        sid for sid, state in session_state.items()
        if state.last_updated < cutoff
    ]
    for sid in to_remove:
        del session_state[sid]


# ==================== CHORD COACHING LOGIC ====================

@app.function(image=image, mounts=[jass_mount])
def suggest_next_chords(chroma: list[int], key: str = "C", difficulty: int = 1):
    """
    Get chord suggestions based on current chord and difficulty.
    Uses your existing TIS index.
    """
    import sys
    sys.path.insert(0, "/root")
    
    from jass.tis_index import TISIndex
    from jass.chord_suggestion import suggest_chords
    
    # Load index
    tis_idx = TISIndex.from_npz("/root/jass/tis_index.npz")
    
    # Get suggestions with varying difficulty
    top_n = max(3, difficulty + 2)  # More suggestions at higher difficulty
    goal = "resolve" if difficulty < 3 else "tension"
    
    result = suggest_chords(
        chroma=chroma,
        key=key,
        index=tis_idx,
        top=top_n,
        goal=goal
    )
    
    return result


def generate_exercise(
    session: SessionState,
    chord_played: str,
    pattern_detected: str | None
) -> str:
    """
    Generate personalized exercise based on session history and patterns.
    """
    # First turn - basic guidance
    if len(session.history) == 0:
        return "Try guide tones (3rd and 7th) for smooth voice leading"
    
    # Pattern detected - escalate difficulty
    if pattern_detected == "ii-V progression":
        session.difficulty = min(5, session.difficulty + 1)
        if session.difficulty == 2:
            return "Nice ii-V! Try adding a tritone sub (♭II7) instead of V7 next time"
        elif session.difficulty == 3:
            return "Try extending the V7 with alterations (♭9, ♯9, ♭13)"
        else:
            return "Explore modal interchange - borrow from parallel minor"
    
    if pattern_detected == "tritone substitution":
        return "Excellent tritone sub! Keep the E-B guide tones and resolve to Imaj7"
    
    # Progressive difficulty based on session length
    turn_count = len(session.history)
    if turn_count > 3:
        return "Try a surprise modulation - pivot to a new key center"
    elif turn_count > 2:
        return "Focus on chromatic voice leading between chords"
    else:
        return "Keep exploring voice leading - move each note by the smallest interval"


# ==================== API ENDPOINTS ====================

@app.function(
    image=image,
    mounts=[jass_mount],
    secrets=[
        modal.Secret.from_dict({
            "PERPLEXITY_API_KEY": "dummy",  # Replace with modal.Secret.from_name()
        })
    ],
)
@modal.web_endpoint(method="POST")
def process_turn(data: dict):
    """
    Process a single turn in the multi-turn conversation.
    
    Request body:
    {
        "session_id": "unique-session-id",
        "chord_name": "Dm7",
        "chroma": [0, 0, 1, 0, 0, 1, 0, 1, 0, 1, 0, 0],
        "key": "C"
    }
    
    Response:
    {
        "suggestions": [...],
        "exercise": "...",
        "feedback": "...",
        "difficulty": 2,
        "turn_number": 3
    }
    """
    # Cleanup old sessions periodically
    cleanup_old_sessions()
    
    # Get or create session
    session_id = data.get("session_id")
    if not session_id:
        return {"error": "session_id required"}, 400
    
    session = get_or_create_session(session_id)
    
    chord_name = data.get("chord_name")
    chroma = data.get("chroma")
    key = data.get("key", "C")
    
    # Detect if user followed a pattern
    pattern = session.detect_pattern(chord_name)
    if pattern and pattern not in session.patterns_detected:
        session.patterns_detected.append(pattern)
    
    # Get chord suggestions
    suggestions_result = suggest_next_chords.remote(
        chroma=chroma,
        key=key,
        difficulty=session.difficulty
    )
    
    suggestions = suggestions_result.get("results", [])
    
    # Generate personalized exercise
    exercise = generate_exercise(session, chord_name, pattern)
    
    # Generate feedback based on context
    feedback = ""
    if pattern:
        feedback = f"Great! You played a {pattern}."
    elif len(session.history) > 0:
        feedback = "Interesting choice!"
    else:
        feedback = "Let's begin! Play along with the suggestions."
    
    # Record this turn
    session.add_turn(chord_name, suggestions, exercise)
    
    return {
        "suggestions": [
            {
                "name": s.get("name"),
                "notes": s.get("notes"),
                "tension": s.get("tension"),
            }
            for s in suggestions
        ],
        "exercise": exercise,
        "feedback": feedback,
        "pattern_detected": pattern,
        "difficulty": session.difficulty,
        "turn_number": len(session.history),
    }


@app.function()
@modal.web_endpoint(method="GET")
def get_session(session_id: str):
    """Get current session state."""
    session = session_state.get(session_id)
    if not session:
        return {"error": "Session not found"}, 404
    
    return session.to_dict()


@app.function()
@modal.web_endpoint(method="POST")
def reset_session(session_id: str):
    """Reset a session."""
    if session_id in session_state:
        del session_state[session_id]
    return {"status": "reset", "session_id": session_id}


# ==================== SONG RECOMMENDATIONS (Async) ====================

@app.function(
    image=image,
    secrets=[
        modal.Secret.from_name("perplexity-api"),
        modal.Secret.from_name("spotify-api"),
    ],
    timeout=60,
)
@modal.web_endpoint(method="POST")
async def recommend_songs_async(data: dict):
    """
    Async endpoint for song recommendations.
    Handles high load without blocking.
    
    Request: {"chord_progression": "C6 -> Am7 -> Dm7 -> G7"}
    """
    import os
    import asyncio
    from perplexityai import Perplexity
    
    chord_progression = data.get("chord_progression", "")
    
    if not chord_progression:
        return {"error": "chord_progression required"}, 400
    
    # Query Perplexity
    client = Perplexity(api_key=os.environ.get("PERPLEXITY_API_KEY"))
    
    prompt = (
        "Return EXACTLY 5 lines. Each line must be: Song Title - Artist Name. "
        "No numbering, bullets, or extra text.\n"
        f"Chord progression: {chord_progression}"
    )
    
    completion = await asyncio.to_thread(
        client.chat.completions.create,
        model="sonar-pro",
        messages=[{"role": "user", "content": prompt}]
    )
    
    response_text = completion.choices[0].message.content
    
    # Parse songs
    songs = []
    for line in response_text.split("\n"):
        line = line.strip()
        if " - " in line and len(line) > 5:
            songs.append(line)
    
    return {
        "chord_progression": chord_progression,
        "songs": songs[:5],
    }


# ==================== LOCAL TESTING ====================

@app.local_entrypoint()
def test():
    """Test the multi-turn system locally."""
    import uuid
    
    session_id = str(uuid.uuid4())
    test_chords = [
        ("Dm7", [0, 0, 1, 0, 0, 1, 0, 1, 0, 1, 0, 0]),
        ("G7", [0, 0, 1, 0, 0, 1, 0, 1, 0, 0, 1, 0]),
        ("Db7", [0, 1, 0, 0, 1, 0, 1, 0, 1, 0, 0, 0]),  # Tritone sub
    ]
    
    print("🎹 Testing Multi-Turn Chord Coaching\n")
    
    for i, (chord_name, chroma) in enumerate(test_chords, 1):
        print(f"Turn {i}: Playing {chord_name}")
        
        result = process_turn.remote({
            "session_id": session_id,
            "chord_name": chord_name,
            "chroma": chroma,
            "key": "C",
        })
        
        print(f"  Feedback: {result['feedback']}")
        print(f"  Exercise: {result['exercise']}")
        print(f"  Difficulty: {result['difficulty']}")
        print(f"  Suggestions: {[s['name'] for s in result['suggestions']]}")
        if result.get('pattern_detected'):
            print(f"  ✓ Pattern: {result['pattern_detected']}")
        print()
    
    # Get final session state
    final_state = get_session.remote(session_id)
    print(f"Session completed: {len(final_state['history'])} turns")
    print(f"Patterns detected: {final_state['patterns_detected']}")
