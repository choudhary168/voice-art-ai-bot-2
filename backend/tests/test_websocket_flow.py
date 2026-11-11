import json
import pytest
from starlette.testclient import TestClient

from backend.main import app
from backend.config import settings


def test_health_endpoint():
    client = TestClient(app)
    response = client.get("/health")
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "healthy"
    assert data["model"] == settings.gemini_model
    assert data["audio_input_rate"] == 16000
    assert data["audio_output_rate"] == 24000


def test_knowledge_rest_endpoints():
    client = TestClient(app)
    # Add new doc
    res = client.post("/api/knowledge", json={
        "title": "Refund Policy",
        "content": "Full refund within 14 days of purchase.",
        "source": "billing-faq"
    })
    assert res.status_code == 200
    assert res.json()["status"] == "success"

    # Get docs
    res2 = client.get("/api/knowledge")
    assert res2.status_code == 200
    assert any(d["title"] == "Refund Policy" for d in res2.json()["documents"])


def test_websocket_text_and_audio_flow(monkeypatch):
    # Keep websocket tests deterministic and never make a paid Live API call,
    # even when a developer has credentials in backend/.env.
    monkeypatch.setattr(settings, "gemini_api_key", "")
    client = TestClient(app)
    with client.websocket_connect("/ws/live") as ws:
        # 1. Send session.start
        ws.send_text(json.dumps({
            "type": "session.start",
            "payload": {
                "system_instruction": "You are a test assistant.",
                "voice_name": "Puck"
            }
        }))

        # Expect session.ready event
        msg1 = json.loads(ws.receive_text())
        assert msg1["type"] == "session.ready"
        assert msg1["payload"]["model"]
        assert msg1["payload"]["output_sample_rate"] == 24000

        # The agent greets immediately after session setup, without user input.
        greeting_events = []
        while True:
            event = json.loads(ws.receive_text())
            greeting_events.append(event)
            if event["type"] == "response.completed":
                break
        greeting_text = " ".join(
            event["payload"]["text"]
            for event in greeting_events
            if event["type"] == "transcript.output"
        )
        assert "Namaste!" in greeting_text
        assert any(event["type"] == "audio.chunk" for event in greeting_events)

        # 2. Send text message
        ws.send_text(json.dumps({
            "type": "text.message",
            "payload": {"text": "What is the capital of India?"}
        }))

        # Read streamed responses
        received_types = set()
        for _ in range(60):
            try:
                raw = ws.receive_text()
                event = json.loads(raw)
                received_types.add(event["type"])
                if event["type"] == "response.completed":
                    break
            except Exception:
                break

        assert "response.started" in received_types
        assert "transcript.output" in received_types
        assert "audio.chunk" in received_types
        assert "response.completed" in received_types

        # 3. Send session.stop
        ws.send_text(json.dumps({
            "type": "session.stop",
            "payload": {"reason": "test_complete"}
        }))

        closed_msg = json.loads(ws.receive_text())
        assert closed_msg["type"] == "session.closed"
