"""
Integration guide: Connect your FastAPI backend to Modal endpoints.

Option 1: Direct Modal calls (recommended for production)
Option 2: Hybrid - FastAPI for MIDI, Modal for AI/coaching
"""
import os
import httpx
import asyncio

# ==================== MODAL CLIENT ====================

class ModalCoachClient:
    """Client for calling Modal chord coaching endpoints."""
    
    def __init__(self, modal_url: str):
        """
        Args:
            modal_url: Your Modal deployment URL
                      e.g., "https://yourname--jass-chord-coach-process-turn.modal.run"
        """
        self.base_url = modal_url
        self.client = httpx.AsyncClient(timeout=30.0)
    
    async def process_turn(
        self,
        session_id: str,
        chord_name: str,
        chroma: list[int],
        key: str = "C"
    ) -> dict:
        """Process a chord and get suggestions + exercise."""
        response = await self.client.post(
            f"{self.base_url}/process_turn",
            json={
                "session_id": session_id,
                "chord_name": chord_name,
                "chroma": chroma,
                "key": key,
            }
        )
        response.raise_for_status()
        return response.json()
    
    async def get_session(self, session_id: str) -> dict:
        """Get session history and state."""
        response = await self.client.get(
            f"{self.base_url}/get_session",
            params={"session_id": session_id}
        )
        response.raise_for_status()
        return response.json()
    
    async def reset_session(self, session_id: str) -> dict:
        """Reset a session."""
        response = await self.client.post(
            f"{self.base_url}/reset_session",
            json={"session_id": session_id}
        )
        response.raise_for_status()
        return response.json()


# ==================== INTEGRATION WITH YOUR FASTAPI ====================

# Add this to your backend/main.py:

"""
# Add at top of main.py
from modal_integration import ModalCoachClient

# Initialize Modal client
modal_coach = None
if os.environ.get("MODAL_ENDPOINT_URL"):
    modal_coach = ModalCoachClient(os.environ["MODAL_ENDPOINT_URL"])

# Add new endpoint
@app.post("/coach-turn")
async def coach_turn(data: dict):
    '''
    Multi-turn chord coaching endpoint.
    
    Request:
    {
        "session_id": "uuid",
        "chord_name": "Dm7",
        "chroma": [0, 0, 1, ...]
    }
    '''
    if not modal_coach:
        return {"error": "Modal coaching not configured"}, 503
    
    result = await modal_coach.process_turn(
        session_id=data["session_id"],
        chord_name=data["chord_name"],
        chroma=data["chroma"],
        key=data.get("key", "C")
    )
    
    return result


@app.get("/coach-session/{session_id}")
async def get_coach_session(session_id: str):
    '''Get coaching session history.'''
    if not modal_coach:
        return {"error": "Modal coaching not configured"}, 503
    
    return await modal_coach.get_session(session_id)
"""


# ==================== FRONTEND INTEGRATION ====================

# Add this to your frontend/src/app/page.tsx (or create new coaching page):

"""
// Add to state
const [coachingSession, setCoachingSession] = useState<string | null>(null);
const [coachFeedback, setCoachFeedback] = useState<string>("");
const [exercise, setExercise] = useState<string>("");

// Enable coaching mode
const startCoaching = async () => {
  const sessionId = crypto.randomUUID();
  setCoachingSession(sessionId);
  setCoachFeedback("Coaching mode enabled! Play a chord to begin.");
};

// When chord is detected
useEffect(() => {
  if (!coachingSession || !lastChord) return;
  
  // Send to coaching endpoint
  fetch("http://localhost:8000/coach-turn", {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({
      session_id: coachingSession,
      chord_name: lastChord.name,
      chroma: lastChord.chroma,
    })
  })
    .then(res => res.json())
    .then(data => {
      setCoachFeedback(data.feedback);
      setExercise(data.exercise);
      // Update suggestions with coaching-aware list
      setSuggestions(data.suggestions);
    });
}, [lastChord]);

// UI
<div className="coaching-panel">
  {!coachingSession ? (
    <button onClick={startCoaching}>Start Coaching Session</button>
  ) : (
    <>
      <p className="feedback">{coachFeedback}</p>
      <p className="exercise">{exercise}</p>
      <button onClick={() => setCoachingSession(null)}>End Session</button>
    </>
  )}
</div>
"""


# ==================== DEPLOYMENT STEPS ====================

def deployment_guide():
    print("""
    🚀 DEPLOYMENT STEPS
    
    1. Set up Modal secrets:
       modal secret create perplexity-api PERPLEXITY_API_KEY=xxx
       modal secret create spotify-api SPOTIFY_CLIENT_ID=xxx SPOTIFY_CLIENT_SECRET=yyy
    
    2. Deploy to Modal:
       modal deploy backend/modal_app.py
       
       This will output URLs like:
       ✓ process_turn: https://yourname--jass-chord-coach-process-turn.modal.run
    
    3. Add Modal URL to your .env:
       MODAL_ENDPOINT_URL=https://yourname--jass-chord-coach-process-turn.modal.run
    
    4. Test locally:
       modal serve backend/modal_app.py
       # Then call endpoints at http://localhost:8000
    
    5. Monitor usage:
       modal app logs jass-chord-coach
    
    📊 SCALING BEHAVIOR
    
    - Each function runs in isolated container
    - Auto-scales to 0 when idle (no cost)
    - Scales up based on request volume
    - In-memory state persists ~10 min per container
    
    💡 UPGRADE TO PERSISTENT STATE
    
    For production, replace in-memory dict with Modal Dict:
    
    from modal import Dict
    session_dict = Dict.lookup("jass-sessions", create_if_missing=True)
    
    # Replace session_state with:
    session_dict[session_id] = session.to_dict()
    
    This persists across container restarts.
    """)


# ==================== LOCAL TESTING ====================

async def test_modal_integration():
    """Test Modal endpoints locally."""
    import uuid
    
    # You need to run: modal serve backend/modal_app.py first
    client = ModalCoachClient("http://localhost:8000")
    
    session_id = str(uuid.uuid4())
    
    print("Testing multi-turn coaching...\n")
    
    # Turn 1: Dm7
    result1 = await client.process_turn(
        session_id=session_id,
        chord_name="Dm7",
        chroma=[0, 0, 1, 0, 0, 1, 0, 1, 0, 1, 0, 0],
    )
    print(f"Turn 1: {result1['feedback']}")
    print(f"Exercise: {result1['exercise']}\n")
    
    # Turn 2: G7 (completing ii-V)
    result2 = await client.process_turn(
        session_id=session_id,
        chord_name="G7",
        chroma=[0, 0, 1, 0, 0, 1, 0, 1, 0, 0, 1, 0],
    )
    print(f"Turn 2: {result2['feedback']}")
    print(f"Exercise: {result2['exercise']}")
    print(f"Pattern: {result2.get('pattern_detected')}\n")
    
    # Get session history
    session = await client.get_session(session_id)
    print(f"Session history: {len(session['history'])} turns")
    print(f"Detected patterns: {session['patterns_detected']}")


if __name__ == "__main__":
    # Print deployment guide
    deployment_guide()
    
    # Uncomment to test:
    # asyncio.run(test_modal_integration())
