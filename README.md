# Gemini 3.8 Live Real-Time AI Voice Agent

A complete, production-grade, sub-second latency real-time voice and text conversational agent built with **Gemini 3.8 Live** as the unified multimodal model.

The agent accepts both continuous microphone speech (16 kHz PCM) and typed text, answers general and domain questions natively, and streams both written transcripts and 24 kHz speech back to the browser simultaneously.

---

## Architecture

```
┌────────────────────────────────────────────────────────────────────────┐
│                        React Frontend (Vite + TS)                      │
│                                                                        │
│  [Microphone] ──(16kHz PCM)──> [Web Audio API] ──> [WebSocket Client]  │
│                                                            ▲           │
│  [Speaker Playback] <──(24kHz PCM)── [Web Audio Queue] ────┤           │
│  [Live Transcript Feed] <──────────────────────────────────┤           │
│  [Telemetry & Latency Panel] <─────────────────────────────┘           │
└──────────────────────────────────┬─────────────────────────────────────┘
                                   │ Bidirectional WebSocket (/ws/live)
                                   ▼
┌────────────────────────────────────────────────────────────────────────┐
│                         FastAPI Backend                                │
│                                                                        │
│   [api/websocket.py] ────> [core/session_manager.py]                   │
│                                     │                                  │
│                                     ▼                                  │
│                          [core/orchestrator.py]                        │
│                           │                  │                         │
│             (Context)     ▼                  ▼   (Streaming Events)    │
│      [services/knowledge.py]       [providers/gemini_live.py]          │
└──────────────────────────────────────────────┬─────────────────────────┘
                                               │ Asynchronous Streaming
                                               ▼
┌────────────────────────────────────────────────────────────────────────┐
│                     Google Gemini Live API                             │
│                  Model: gemini-3.8-live                                │
│    - Native Audio In (16kHz PCM)   - Native Audio Out (24kHz PCM)     │
│    - User Speech Transcription     - Model Output Transcription        │
│    - Voice Activity Detection      - Native Multilingual Processing    │
└────────────────────────────────────────────────────────────────────────┘
```

### Key Architectural Strengths
1. **Unified Multimodal Path**: No cascading STT → LLM → TTS pipelines. Audio is received and produced natively by Gemini Live, achieving sub-second time-to-first-audio (TTFB).
2. **Gapless Audio Playback**: The frontend schedules 24 kHz 16-bit PCM chunks as soon as they arrive on Web Audio's monotonic timeline (`AudioContext.currentTime`).
3. **Instant Interruption**: User interruptions immediately clear the audio queue on the client and notify the backend to cancel stale turns.
4. **Clean Knowledge Extension Point**: Domain knowledge (FAQs, product documentation, user profiles) is abstracted into `services/knowledge.py` and can be enriched dynamically at runtime without restarting the application or rebuilding the Live pipeline.

---

## Directory Structure

```
gemini-voice-agent/
├── backend/
│   ├── .env.example              # Environment variables template
│   ├── .env                      # Local configuration
│   ├── config.py                 # Pydantic Settings with env validation
│   ├── main.py                   # FastAPI setup, CORS, lifespan, /health & /api/knowledge
│   ├── schemas/
│   │   ├── __init__.py
│   │   └── events.py             # Strongly-typed WebSocket client/server contract
│   ├── api/
│   │   ├── __init__.py
│   │   └── websocket.py          # /ws/live endpoint & message routing
│   ├── core/
│   │   ├── __init__.py
│   │   ├── orchestrator.py       # Turn coordination, metrics, and event pump
│   │   └── session_manager.py    # Session lifecycle & provider instantiation
│   ├── providers/
│   │   ├── __init__.py
│   │   ├── base.py               # LiveModelProvider abstract interface
│   │   ├── gemini_live.py        # Official google-genai Gemini Live integration
│   │   └── mock_live.py          # Offline/unit-testing provider
│   ├── services/
│   │   ├── __init__.py
│   │   ├── audio.py              # PCM encoding/decoding, framing & resampling
│   │   └── knowledge.py          # Abstract knowledge provider & dynamic FAQ store
│   └── tests/
│       ├── test_config.py        # Settings validation tests
│       ├── test_events.py        # Typed schema validation tests
│       ├── test_audio_service.py # PCM conversion & RMS tests
│       ├── test_knowledge.py     # Knowledge provider tests
│       └── test_websocket_flow.py# Full WebSocket turn lifecycle test
├── frontend/
│   ├── index.html                # App shell with typography
│   ├── package.json              # React 19, Lucide, Vite
│   ├── tsconfig.json             # TypeScript strict configuration
│   ├── vite.config.ts            # Vite server & proxy configuration
│   └── src/
│       ├── index.css             # Vanilla CSS design system, dark mode & tokens
│       ├── main.tsx              # React mounting point
│       ├── App.tsx               # Main layout & Knowledge injection modal
│       ├── types/
│       │   └── events.ts         # Typed TypeScript WebSocket contract
│       ├── services/
│       │   ├── websocket.ts      # WebSocket connection & event emitter
│       │   ├── audioCapture.ts   # 16 kHz PCM microphone capture & echo cancellation
│       │   └── audioPlayback.ts  # 24 kHz gapless Web Audio scheduler
│       ├── hooks/
│       │   └── useVoiceAgent.ts  # Session state, audio streaming & turn management
│       └── components/
│           ├── AudioPlayer.tsx   # Streaming audio playback state & volume controls
│           ├── VoiceControls.tsx # Mic button, connect switch, and text input
│           ├── ChatMessages.tsx  # Partial & final conversation transcript feed
│           ├── Visualizer.tsx    # Responsive canvas audio wave visualizer
│           └── LatencyDiagnostics.tsx # Real-time latency metrics & telemetry
├── .gitignore
└── README.md
```

---

## WebSocket Event Contract

| Direction | Event Name | Description | Key Payload Fields |
|---|---|---|---|
| **Client → Server** | `session.start` | Initializes live session | `system_instruction`, `voice_name`, `client_timestamp` |
| **Client → Server** | `audio.chunk` | Streams mic audio chunk | `data` (Base64 PCM 16kHz), `seq`, `sample_rate` |
| **Client → Server** | `audio.end` | Signals user stopped speaking | `timestamp` |
| **Client → Server** | `text.message` | Submits typed text query | `text`, `timestamp` |
| **Client → Server** | `response.interrupt`| Cancels current agent turn | `turn_id`, `timestamp` |
| **Client → Server** | `session.stop` | Closes session | `reason`, `timestamp` |
| **Server → Client** | `session.ready` | Confirms session initialized | `session_id`, `model`, `voice`, `input_sample_rate`, `output_sample_rate` |
| **Server → Client** | `transcript.input` | User speech transcription | `text`, `is_final`, `timestamp` |
| **Server → Client** | `transcript.output`| Spoken agent transcription | `text`, `is_final`, `turn_id`, `timestamp` |
| **Server → Client** | `audio.chunk` | Synthesized speech chunk | `data` (Base64 PCM 24kHz), `seq`, `turn_id`, `sample_rate` |
| **Server → Client** | `response.started` | Response generation started | `turn_id`, `timestamp` |
| **Server → Client** | `response.completed`| Turn finished with latency telemetry | `turn_id`, `metrics` (TTFB audio ms, transcript ms, duration ms) |
| **Server → Client** | `session.error` | Error notification | `code`, `message`, `recoverable` |
| **Server → Client** | `session.closed` | Session terminated | `reason`, `timestamp` |

---

## Setup and Run Instructions (Windows PowerShell)

### Prerequisites
- Python 3.12+ (Python 3.13.5 supported)
- Node.js v20+ (Node v24.18.0 & npm 11.16.0 supported)
- A Google Gemini API key from [Google AI Studio](https://aistudio.google.com/)

---

### Step 1: Configure Environment Variables

1. Open PowerShell and navigate to the project directory:
   ```powershell
   cd "c:\Users\Vansh Choudhary\OneDrive - Ajay Kumar Garg Engineering College\Desktop\gemini voice agent"
   ```

2. Open `backend/.env` in your text editor and set your `GEMINI_API_KEY`:
   ```env
   GEMINI_API_KEY=your_actual_gemini_api_key_here
   GEMINI_MODEL=gemini-3.8-live
   VOICE_NAME=Puck
   PORT=8000
   ```
   *(Note: If `GEMINI_API_KEY` is not provided, the backend automatically runs in offline mock mode, allowing full UI and audio pipeline verification without crashing).*

---

### Step 2: Run Backend Automated Tests

Run the full pytest test suite:
```powershell
python -m pytest backend/tests -v
```
You should see all 14 tests pass:
```
backend/tests/test_audio_service.py::test_encode_decode_pcm PASSED
backend/tests/test_audio_service.py::test_duration_calculation PASSED
backend/tests/test_audio_service.py::test_rms_calculation PASSED
backend/tests/test_audio_service.py::test_resampling PASSED
backend/tests/test_config.py::test_default_config PASSED
backend/tests/test_config.py::test_cors_origins_parsing PASSED
backend/tests/test_events.py::test_client_event_validation PASSED
backend/tests/test_events.py::test_audio_chunk_event PASSED
backend/tests/test_events.py::test_server_event_constructors PASSED
backend/tests/test_knowledge.py::test_knowledge_provider PASSED
backend/tests/test_knowledge.py::test_user_profile PASSED
backend/tests/test_websocket_flow.py::test_health_endpoint PASSED
backend/tests/test_websocket_flow.py::test_knowledge_rest_endpoints PASSED
backend/tests/test_websocket_flow.py::test_websocket_text_and_audio_flow PASSED
```

---

### Step 3: Start the Backend Server

Start Uvicorn with:
```powershell
python -m uvicorn backend.main:app --host 0.0.0.0 --port 8000 --reload
```
You should see:
```
INFO: Starting Gemini Real-Time Voice Agent Backend...
INFO: Model: gemini-3.8-live | Voice: Puck | API Key Configured: True
INFO: Uvicorn running on http://0.0.0.0:8000
```
Verify the health endpoint in your browser or curl:
```powershell
Invoke-RestMethod http://localhost:8000/health
```

---

### Step 4: Start the Frontend Application

Open a **second PowerShell terminal** and run:
```powershell
cd "c:\Users\Vansh Choudhary\OneDrive - Ajay Kumar Garg Engineering College\Desktop\gemini voice agent\frontend"
npm run dev
```
Open your browser at:
`http://localhost:5173/`

---

## Manual Browser Testing Guide

### 1. Connecting to Session
- Click **Start Session**.
- The status indicator switches to `Connected` (green pulse), and the audio engine initializes.

### 2. Testing Text Input (Text + Speech Output)
- Type a question in the input box: *"Namaste! Kaise ho aap? Explain quantum computing in Hinglish."*
- Click **Send** or press Enter.
- Observe:
  - User message appears immediately in the transcript feed.
  - Model response starts streaming within hundreds of milliseconds.
  - Spoken audio plays immediately via Web Audio at 24 kHz PCM without waiting for the full sentence.
  - The latency diagnostics panel records and displays **First Audio Latency (ms)**, **Output Transcription Latency (ms)**, and **Turn Duration (ms)**.

### 3. Testing Microphone Speech Input
- Click the big emerald button: **Start Voice Mode**.
- Allow microphone permissions in your browser.
- Speak naturally: *"What is the difference between supervised and unsupervised learning?"*
- Observe:
  - The visualizer displays green wave activity reflecting your voice amplitude.
  - User speech transcription (`transcript.input`) updates in real-time.
  - When you finish speaking, the model begins answering automatically through native Voice Activity Detection (VAD).

### 4. Testing Interruption
- While the agent is speaking, click the **Interrupt** button (or start speaking if in voice mode).
- Notice that audio playback halts instantaneously, queued chunks are cleared, and stale speech is dropped.

### 5. Dynamic Knowledge Injection
- Click the **Knowledge Store** button in the header.
- Enter a custom title and FAQ excerpt (e.g. *"Campus Library Timings: The library is open Monday through Saturday from 8 AM to 10 PM"*).
- Click **Add Document**.
- Ask the agent: *"When does the library close?"*
- The agent references the injected context dynamically!

---

## Troubleshooting & FAQ

| Problem | Cause | Solution |
|---|---|---|
| `GEMINI_API_KEY is not set` | No API key in `backend/.env` | Add your Gemini API key to `backend/.env`. The app falls back to mock mode so UI remains testable. |
| Microphone permission denied | Browser blocked microphone access | In Chrome/Edge, click the lock icon in the address bar and select **Allow** for Microphone. |
| Audio glitches or delay | Browser tab sleeping or audio context suspended | Click anywhere on the interface or toggle Mute to resume Web Audio context. |
| Model quota or rate limit | Free tier quota exceeded on Gemini Live | Switch model in `backend/.env` to `gemini-2.0-flash-exp` or verify Google AI Studio project quotas. |
