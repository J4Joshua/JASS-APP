# JASS-APP

Real-time MIDI chord detection and suggestion engine. Play chords on a MIDI piano and get intelligent next-chord suggestions streamed to a web UI via WebSocket.

## Prerequisites

- Python 3.10+
- Node.js 18+
- A MIDI controller (optional — the backend can run without one)

## Setup

### Backend

```bash
cd backend
pip install -r requirements.txt
```

### Frontend

```bash
cd frontend
npm install
```

## Running

### 1. Start the backend

```bash
python backend/main.py
```

The WebSocket server starts on `ws://localhost:8000/ws`.

To run without a MIDI device:

```bash
DISABLE_MIDI=1 python backend/main.py
```

### 2. Start the frontend

```bash
cd frontend
npm run dev
```

Opens at `http://localhost:3000`.

## Configuration

### Environment Variables

Create a `.env` file in the `backend` directory with the following variables:

```bash
# Perplexity API Key (required for song recommendations)
PERPLEXITY_API_KEY=your_api_key_here

# Spotify API Credentials (optional - for album art and artist info)
SPOTIFY_CLIENT_ID=your_client_id_here
SPOTIFY_CLIENT_SECRET=your_client_secret_here

# Optional: Disable MIDI input
DISABLE_MIDI=1
```

#### Getting Perplexity API Key
1. Visit https://www.perplexity.ai/
2. Sign up or log in
3. Navigate to your account settings and generate an API key

#### Getting Spotify Credentials
1. Visit https://developer.spotify.com/dashboard
2. Log in or create a developer account
3. Create a new application
4. Copy the **Client ID** and **Client Secret**
5. Add them to your `.env` file

**Note**: Spotify credentials are optional. Without them, song recommendations will still work but won't display album art or artist information.

## Project Structure

```
backend/
  main.py              # FastAPI WebSocket server + MIDI capture
  jass/                 # Chord suggestion & tonal tension engine
  pianomidi/            # MIDI input & chord detection utilities
  requirements.txt

frontend/              # Next.js + React + Tailwind CSS
  src/app/
```