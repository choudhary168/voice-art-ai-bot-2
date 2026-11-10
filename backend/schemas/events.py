import time
from enum import Enum
from typing import Any, Dict, List, Optional, Union
from pydantic import BaseModel, Field, field_validator
from backend.config import resolve_live_voice_name


class ClientEventType(str, Enum):
    SESSION_START = "session.start"
    AUDIO_CHUNK = "audio.chunk"
    AUDIO_END = "audio.end"
    TEXT_MESSAGE = "text.message"
    RESPONSE_INTERRUPT = "response.interrupt"
    SESSION_STOP = "session.stop"


class ServerEventType(str, Enum):
    SESSION_READY = "session.ready"
    TRANSCRIPT_INPUT = "transcript.input"
    TRANSCRIPT_OUTPUT = "transcript.output"
    AUDIO_CHUNK = "audio.chunk"
    RESPONSE_STARTED = "response.started"
    RESPONSE_COMPLETED = "response.completed"
    SESSION_ERROR = "session.error"
    SESSION_CLOSED = "session.closed"


# --- Client Payloads ---

class SessionStartPayload(BaseModel):
    system_instruction: Optional[str] = None
    voice_name: Optional[str] = None
    client_timestamp: float = Field(default_factory=time.time)

    @field_validator("voice_name", mode="before")
    @classmethod
    def validate_voice_name(cls, value: object) -> Optional[str]:
        if value is None:
            return None
        return resolve_live_voice_name(value)


class AudioChunkPayload(BaseModel):
    data: str  # Base64 encoded raw PCM audio (16-bit little-endian mono, 16kHz)
    seq: int = 0
    sample_rate: int = 16000
    timestamp: float = Field(default_factory=time.time)


class AudioEndPayload(BaseModel):
    timestamp: float = Field(default_factory=time.time)


class TextMessagePayload(BaseModel):
    text: str
    timestamp: float = Field(default_factory=time.time)


class ResponseInterruptPayload(BaseModel):
    turn_id: Optional[str] = None
    timestamp: float = Field(default_factory=time.time)


class SessionStopPayload(BaseModel):
    reason: Optional[str] = "user_initiated"
    timestamp: float = Field(default_factory=time.time)


# --- Generic Client Event Container ---

class ClientEvent(BaseModel):
    type: ClientEventType
    payload: Dict[str, Any] = Field(default_factory=dict)


# --- Server Payloads & Metrics ---

class LatencyMetrics(BaseModel):
    client_session_start: Optional[float] = None
    gemini_connected: Optional[float] = None
    first_input_sent: Optional[float] = None
    first_input_transcription: Optional[float] = None
    first_model_response: Optional[float] = None
    first_output_transcription: Optional[float] = None
    first_audio_chunk: Optional[float] = None
    turn_completed: Optional[float] = None
    # Derived intervals in milliseconds
    e2e_first_audio_ms: Optional[float] = None
    e2e_first_transcription_ms: Optional[float] = None
    total_turn_duration_ms: Optional[float] = None


class SessionReadyPayload(BaseModel):
    session_id: str
    model: str
    voice: str
    input_sample_rate: int = 16000
    output_sample_rate: int = 24000
    channels: int = 1
    bits_per_sample: int = 16
    capabilities: List[str] = Field(default_factory=lambda: ["audio_input", "audio_output", "text_input", "transcription", "bilingual_hindi_english"])


class TranscriptInputPayload(BaseModel):
    text: str
    is_final: bool = False
    timestamp: float = Field(default_factory=time.time)


class TranscriptOutputPayload(BaseModel):
    text: str
    is_final: bool = False
    turn_id: str
    timestamp: float = Field(default_factory=time.time)


class ServerAudioChunkPayload(BaseModel):
    data: str  # Base64 encoded raw PCM audio (16-bit little-endian mono, 24kHz)
    seq: int
    turn_id: str
    sample_rate: int = 24000
    timestamp: float = Field(default_factory=time.time)


class ResponseStartedPayload(BaseModel):
    turn_id: str
    timestamp: float = Field(default_factory=time.time)


class ResponseCompletedPayload(BaseModel):
    turn_id: str
    timestamp: float = Field(default_factory=time.time)
    metrics: LatencyMetrics = Field(default_factory=LatencyMetrics)


class SessionErrorPayload(BaseModel):
    code: str
    message: str
    recoverable: bool = True
    timestamp: float = Field(default_factory=time.time)


class SessionClosedPayload(BaseModel):
    reason: str
    timestamp: float = Field(default_factory=time.time)


# --- Generic Server Event Container ---

class ServerEvent(BaseModel):
    type: ServerEventType
    payload: Dict[str, Any]

    @classmethod
    def session_ready(cls, session_id: str, model: str, voice: str, **kwargs) -> "ServerEvent":
        payload = SessionReadyPayload(session_id=session_id, model=model, voice=voice, **kwargs)
        return cls(type=ServerEventType.SESSION_READY, payload=payload.model_dump())

    @classmethod
    def transcript_input(cls, text: str, is_final: bool = False) -> "ServerEvent":
        payload = TranscriptInputPayload(text=text, is_final=is_final)
        return cls(type=ServerEventType.TRANSCRIPT_INPUT, payload=payload.model_dump())

    @classmethod
    def transcript_output(cls, text: str, turn_id: str, is_final: bool = False) -> "ServerEvent":
        payload = TranscriptOutputPayload(text=text, turn_id=turn_id, is_final=is_final)
        return cls(type=ServerEventType.TRANSCRIPT_OUTPUT, payload=payload.model_dump())

    @classmethod
    def audio_chunk(cls, data: str, seq: int, turn_id: str, sample_rate: int = 24000) -> "ServerEvent":
        payload = ServerAudioChunkPayload(data=data, seq=seq, turn_id=turn_id, sample_rate=sample_rate)
        return cls(type=ServerEventType.AUDIO_CHUNK, payload=payload.model_dump())

    @classmethod
    def response_started(cls, turn_id: str) -> "ServerEvent":
        payload = ResponseStartedPayload(turn_id=turn_id)
        return cls(type=ServerEventType.RESPONSE_STARTED, payload=payload.model_dump())

    @classmethod
    def response_completed(cls, turn_id: str, metrics: LatencyMetrics) -> "ServerEvent":
        payload = ResponseCompletedPayload(turn_id=turn_id, metrics=metrics)
        return cls(type=ServerEventType.RESPONSE_COMPLETED, payload=payload.model_dump())

    @classmethod
    def error(cls, code: str, message: str, recoverable: bool = True) -> "ServerEvent":
        payload = SessionErrorPayload(code=code, message=message, recoverable=recoverable)
        return cls(type=ServerEventType.SESSION_ERROR, payload=payload.model_dump())

    @classmethod
    def closed(cls, reason: str = "normal_closure") -> "ServerEvent":
        payload = SessionClosedPayload(reason=reason)
        return cls(type=ServerEventType.SESSION_CLOSED, payload=payload.model_dump())
