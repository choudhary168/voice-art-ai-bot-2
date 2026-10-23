import asyncio
import uuid
from typing import AsyncIterator, Optional
from backend.providers.base import LiveModelProvider, ModelEvent, ModelEventType


class MockModelProvider(LiveModelProvider):
    """
    Mock implementation of LiveModelProvider for deterministic unit testing
    and offline validation of orchestrator and WebSocket contracts.
    """

    def __init__(self, model_id: str = "mock-live"):
        self.model_id = model_id
        self._connected: bool = False
        self._event_queue: asyncio.Queue[ModelEvent] = asyncio.Queue()
        self._current_turn_id: str = str(uuid.uuid4())

    @property
    def is_connected(self) -> bool:
        return self._connected

    async def connect(self, system_instruction: Optional[str] = None, voice_name: Optional[str] = None) -> None:
        self._connected = True
        self._current_turn_id = str(uuid.uuid4())
        await self._event_queue.put(
            ModelEvent(type=ModelEventType.CONNECTED, turn_id=self._current_turn_id)
        )

    async def disconnect(self) -> None:
        self._connected = False

    async def send_audio_chunk(self, pcm_bytes: bytes) -> None:
        if not self._connected:
            return
        # Simulate input transcription after receiving audio
        await self._event_queue.put(
            ModelEvent(
                type=ModelEventType.TRANSCRIPT_INPUT,
                text="Hello from simulated speech input",
                is_final=False,
                turn_id=self._current_turn_id
            )
        )

    async def send_audio_end(self) -> None:
        if not self._connected:
            return
        await self._generate_simulated_turn("I heard your voice loud and clear!")

    async def send_text(self, text: str, end_of_turn: bool = True) -> None:
        if not self._connected:
            return
        await self._generate_simulated_turn(f"You asked: {text}. Here is the answer.")

    async def _generate_simulated_turn(self, response_text: str) -> None:
        turn_id = self._current_turn_id
        # Emit transcript
        await self._event_queue.put(
            ModelEvent(
                type=ModelEventType.TRANSCRIPT_OUTPUT,
                text=response_text,
                is_final=True,
                turn_id=turn_id
            )
        )
        # Emit simulated 24kHz PCM silence/tone audio chunk (4800 bytes = 100ms)
        simulated_audio = b"\x00" * 4800
        await self._event_queue.put(
            ModelEvent(
                type=ModelEventType.AUDIO_CHUNK,
                audio_bytes=simulated_audio,
                turn_id=turn_id
            )
        )
        # Turn complete
        await self._event_queue.put(
            ModelEvent(
                type=ModelEventType.TURN_COMPLETE,
                turn_id=turn_id
            )
        )
        self._current_turn_id = str(uuid.uuid4())

    async def interrupt(self) -> None:
        self._current_turn_id = str(uuid.uuid4())
        while not self._event_queue.empty():
            try:
                self._event_queue.get_nowait()
            except asyncio.QueueEmpty:
                break
        await self._event_queue.put(
            ModelEvent(type=ModelEventType.INTERRUPTED, turn_id=self._current_turn_id)
        )

    async def stream_events(self) -> AsyncIterator[ModelEvent]:
        while self._connected or not self._event_queue.empty():
            try:
                event = await asyncio.wait_for(self._event_queue.get(), timeout=0.1)
                yield event
            except asyncio.TimeoutError:
                continue
