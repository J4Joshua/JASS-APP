# Modal Multi-Turn Chord Coaching

This directory contains the Modal deployment for multi-turn chord coaching with state management.

## Quick Start

```bash
# 1. Install Modal
pip install modal

# 2. Authenticate
modal token new

# 3. Create secrets
modal secret create perplexity-api PERPLEXITY_API_KEY=your_key_here
modal secret create spotify-api SPOTIFY_CLIENT_ID=xxx SPOTIFY_CLIENT_SECRET=yyy

# 4. Test locally
modal serve modal_app.py
# Server runs at http://localhost:8000

# 5. Deploy to production
modal deploy modal_app.py
# Outputs live URLs for your endpoints
```

## Architecture

### State Management Options

**Current: In-Memory Dict** (Good for demos/hackathons)
- Persists ~10 minutes after last use
- No setup required
- Resets on container restart

**Upgrade: Modal Dict** (Production-ready)
```python
from modal import Dict
session_dict = Dict.lookup("jass-sessions", create_if_missing=True)
```

**Upgrade: Modal Volume** (Large-scale)
```python
from modal import Volume
vol = Volume.lookup("jass-data", create_if_missing=True)
```

## Multi-Turn Flow

```
Turn 1: User plays Dm7
  ↓
  Agent: "Try guide tones (3rd and 7th)"
  Suggestions: [G7, A7, Fmaj7]

Turn 2: User plays G7 (follows ii-V!)
  ↓
  Agent: "Nice ii-V! Try tritone sub Db7 next time"
  Difficulty: 1 → 2
  Suggestions: [Cmaj7, Db7, Em7]

Turn 3: User plays Db7 (tritone sub!)
  ↓
  Agent: "Excellent! Keep E-B guide tones, resolve to Cmaj9"
  Difficulty: 2 → 3
  Pattern Detected: "tritone substitution"
```

## API Endpoints

### POST `/process_turn`
Process a chord and get coaching feedback.

**Request:**
```json
{
  "session_id": "uuid-string",
  "chord_name": "Dm7",
  "chroma": [0, 0, 1, 0, 0, 1, 0, 1, 0, 1, 0, 0],
  "key": "C"
}
```

**Response:**
```json
{
  "suggestions": [
    {"name": "G7", "notes": ["G", "B", "D", "F"], "tension": 0.65}
  ],
  "exercise": "Try guide tones...",
  "feedback": "Great! You played a ii-V progression.",
  "pattern_detected": "ii-V progression",
  "difficulty": 2,
  "turn_number": 3
}
```

### GET `/get_session?session_id=xxx`
Get session history and state.

### POST `/reset_session`
Reset a session.

### POST `/recommend_songs_async`
Async song recommendation (handles high load).

## Integration with FastAPI

Add to your `backend/main.py`:

```python
from modal_integration import ModalCoachClient

# Initialize
modal_coach = ModalCoachClient(os.environ["MODAL_ENDPOINT_URL"])

@app.post("/coach-turn")
async def coach_turn(data: dict):
    return await modal_coach.process_turn(
        session_id=data["session_id"],
        chord_name=data["chord_name"],
        chroma=data["chroma"]
    )
```

Add to `.env`:
```bash
MODAL_ENDPOINT_URL=https://yourname--jass-chord-coach-process-turn.modal.run
```

## Frontend Integration

```typescript
// Start coaching session
const sessionId = crypto.randomUUID();

// When chord detected
fetch("http://localhost:8000/coach-turn", {
  method: "POST",
  body: JSON.stringify({
    session_id: sessionId,
    chord_name: "Dm7",
    chroma: [0, 0, 1, ...]
  })
}).then(r => r.json()).then(data => {
  console.log(data.feedback);    // "Nice ii-V!"
  console.log(data.exercise);    // "Try tritone sub..."
  console.log(data.suggestions); // Next chord options
});
```

## Cost Estimation

Modal pricing (~$0.30 per CPU hour):
- Each request: ~100-500ms
- Cost per request: ~$0.00001 - $0.00005
- 1000 requests/day: ~$0.50/month
- Scales to 0 when idle

## Testing

```bash
# Run built-in test
modal run modal_app.py

# Test locally with curl
curl -X POST http://localhost:8000/process_turn \
  -H "Content-Type: application/json" \
  -d '{
    "session_id": "test-123",
    "chord_name": "Dm7",
    "chroma": [0,0,1,0,0,1,0,1,0,1,0,0]
  }'
```

## Monitoring

```bash
# View logs
modal app logs jass-chord-coach

# Check function stats
modal app stats jass-chord-coach
```

## Next Steps

1. ✅ Deploy to Modal
2. ✅ Test multi-turn flow
3. 🔄 Add pattern detection (extend `detect_pattern()`)
4. 🔄 Improve difficulty scaling
5. 🔄 Add voice leading analysis
6. 🔄 Upgrade to Modal Dict for persistence
