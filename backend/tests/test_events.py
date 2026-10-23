import pytest
from backend.schemas.events import (
    AudioChunkPayload,
    ClientEvent,
    ClientEventType,
    LatencyMetrics,
    ServerEvent,
    ServerEventType,
    SessionStartPayload,
    TextMessagePayload,
)


def test_client_event_validation():
    # Valid text message event
    raw = {
        "type": "text.message",
        "payload": {"text": "Namaste! How are you?"}
    }
    event = ClientEvent.model_validate(raw)
    assert event.type == ClientEventType.TEXT_MESSAGE
    text_payload = TextMessagePayload.model_validate(event.payload)
    assert text_payload.text == "Namaste! How are you?"


def test_audio_chunk_event():
    raw = {
        "type": "audio.chunk",
        "payload": {
            "data": "AAAA",
            "seq": 1,
            "sample_rate": 16000
        }
    }
    event = ClientEvent.model_validate(raw)
    assert event.type == ClientEventType.AUDIO_CHUNK
    chunk_payload = AudioChunkPayload.model_validate(event.payload)
    assert chunk_payload.seq == 1
    assert chunk_payload.sample_rate == 16000


def test_server_event_constructors():
    ready = ServerEvent.session_ready(session_id="test-123", model="gemini-3.8-live", voice="Puck")
    assert ready.type == ServerEventType.SESSION_READY
    assert ready.payload["session_id"] == "test-123"
    assert ready.payload["output_sample_rate"] == 24000

    metrics = LatencyMetrics(e2e_first_audio_ms=180.5, total_turn_duration_ms=950.0)
    completed = ServerEvent.response_completed(turn_id="turn-abc", metrics=metrics)
    assert completed.type == ServerEventType.RESPONSE_COMPLETED
    assert completed.payload["metrics"]["e2e_first_audio_ms"] == 180.5
