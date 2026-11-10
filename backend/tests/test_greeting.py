import asyncio

import pytest

from backend.core.orchestrator import INITIAL_GREETING, SessionOrchestrator
from backend.providers.mock_live import MockModelProvider
from backend.schemas.events import SessionStartPayload


@pytest.mark.asyncio
async def test_session_starts_with_one_greeting_and_audio_stream():
    events = []
    completed = asyncio.Event()

    async def send_event(event):
        events.append(event)
        if event.type.value == "response.completed":
            completed.set()

    provider = MockModelProvider()
    orchestrator = SessionOrchestrator("greeting-test", provider, send_event)

    await orchestrator.start(SessionStartPayload())
    await completed.wait()
    await orchestrator.start(SessionStartPayload())  # duplicate ready/start signal

    output_text = " ".join(
        event.payload["text"]
        for event in events
        if event.type.value == "transcript.output"
    )
    assert output_text == INITIAL_GREETING
    assert sum(event.type.value == "session.ready" for event in events) == 1
    assert sum(event.type.value == "audio.chunk" for event in events) == 1
    assert sum(event.type.value == "response.completed" for event in events) == 1
    await orchestrator.close()


@pytest.mark.asyncio
async def test_failed_initialization_does_not_mark_greeting_started():
    class FailingProvider(MockModelProvider):
        async def connect(self, system_instruction=None, voice_name=None):
            raise RuntimeError("connection failed")

    events = []

    async def send_event(event):
        events.append(event)

    orchestrator = SessionOrchestrator("failed-test", FailingProvider(), send_event)
    await orchestrator.start(SessionStartPayload())

    assert orchestrator._initial_greeting_started is False
    assert not any(event.type.value == "session.ready" for event in events)
    assert any(event.type.value == "session.error" for event in events)
