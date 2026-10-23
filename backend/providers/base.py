import abc
from enum import Enum
from typing import AsyncIterator, Optional
from pydantic import BaseModel


class ModelEventType(str, Enum):
    CONNECTED = "connected"
    TRANSCRIPT_INPUT = "transcript_input"
    TRANSCRIPT_OUTPUT = "transcript_output"
    AUDIO_CHUNK = "audio_chunk"
    INTERRUPTED = "interrupted"
    TURN_COMPLETE = "turn_complete"
    ERROR = "error"


class ModelEvent(BaseModel):
    type: ModelEventType
    text: Optional[str] = None
    audio_bytes: Optional[bytes] = None
    is_final: bool = False
    turn_id: Optional[str] = None
    error_message: Optional[str] = None


class LiveModelProvider(abc.ABC):
    """Abstract interface for real-time bidirectional streaming model providers."""

    @abc.abstractmethod
    async def connect(self, system_instruction: Optional[str] = None, voice_name: Optional[str] = None) -> None:
        """Establish bidirectional connection with model."""
        pass

    @abc.abstractmethod
    async def disconnect(self) -> None:
        """Close connection cleanly."""
        pass

    @abc.abstractmethod
    async def send_audio_chunk(self, pcm_bytes: bytes) -> None:
        """Send continuous raw 16kHz PCM audio chunk."""
        pass

    @abc.abstractmethod
    async def send_audio_end(self) -> None:
        """Signal that audio speech turn has ended."""
        pass

    @abc.abstractmethod
    async def send_text(self, text: str, end_of_turn: bool = True) -> None:
        """Send a typed text message."""
        pass

    @abc.abstractmethod
    async def interrupt(self) -> None:
        """Signal an interruption to the live session."""
        pass

    @abc.abstractmethod
    async def stream_events(self) -> AsyncIterator[ModelEvent]:
        """Stream real-time events (transcriptions, audio chunks, turn signals) from the model."""
        pass

    @property
    @abc.abstractmethod
    def is_connected(self) -> bool:
        """Return True if connection is currently active."""
        pass
