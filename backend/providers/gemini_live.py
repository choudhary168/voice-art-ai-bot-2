import asyncio
import logging
import re
import uuid
from importlib.metadata import PackageNotFoundError, version
from typing import AsyncIterator, List, Optional
from google import genai
from google.genai import types

from backend.config import DEFAULT_LIVE_VOICE, resolve_live_voice_name, settings
from backend.providers.base import LiveModelProvider, ModelEvent, ModelEventType

logger = logging.getLogger("gemini_live")


def _upstream_rejection_details(error: Exception) -> str:
    """Expose safe HTTP rejection details without logging request URLs or keys."""
    response = getattr(error, "response", None) or getattr(error, "http_response", None)
    if response is None:
        return ""

    details = []
    status = getattr(response, "status_code", None) or getattr(response, "status", None)
    reason = getattr(response, "reason_phrase", None)
    if status is not None:
        details.append(f"upstream_status={status}")
    if reason:
        details.append(f"upstream_reason={str(reason)[:120]}")

    body = getattr(response, "body", None)
    if isinstance(body, bytes):
        body = body.decode("utf-8", errors="replace")
    if body:
        body = re.sub(r"(?i)(api[_ -]?key|key)[\"'=:\s]+[^\"'\s,}]+", r"\1=[REDACTED]", str(body))
        details.append(f"upstream_body={body.strip()[:800]!r}")
    return " " + " ".join(details) if details else ""


def build_live_connect_config(system_instruction: str, voice_name: Optional[str] = None):
    """Build the audio Live API setup with a validated prebuilt voice."""
    voice = resolve_live_voice_name(voice_name)
    return types.LiveConnectConfig(
        response_modalities=["AUDIO"],
        speech_config=types.SpeechConfig(
            voice_config=types.VoiceConfig(
                prebuilt_voice_config=types.PrebuiltVoiceConfig(voice_name=voice)
            )
        ),
        system_instruction=types.Content(
            parts=[types.Part.from_text(text=system_instruction)]
        ),
        input_audio_transcription=types.AudioTranscriptionConfig(),
        output_audio_transcription=types.AudioTranscriptionConfig(),
    )


class GeminiLiveProvider(LiveModelProvider):
    """
    Production implementation of LiveModelProvider using the official
    Google GenAI SDK (google-genai) and Gemini Live API.
    Includes automated retry with exponential backoff and seamless model fallback
    to withstand transient 503 UNAVAILABLE / high demand spikes.
    """

    # Strictly configured for Gemini 3.8 Live
    FALLBACK_MODELS = ["gemini-3.8-live"]

    def __init__(self, model_id: Optional[str] = None, api_key: Optional[str] = None):
        self.model_id = model_id or settings.gemini_model
        self.api_key = api_key or settings.gemini_api_key
        self._client: Optional[genai.Client] = None
        self._session = None
        self._session_context = None
        self._event_queue: asyncio.Queue[ModelEvent] = asyncio.Queue(maxsize=500)
        self._receive_task: Optional[asyncio.Task] = None
        self._is_connected: bool = False
        self._is_closed: bool = False
        self._connect_lock = asyncio.Lock()
        self._current_turn_id: str = str(uuid.uuid4())

    @property
    def is_connected(self) -> bool:
        return self._is_connected and self._session is not None

    async def connect(self, system_instruction: Optional[str] = None, voice_name: Optional[str] = None) -> None:
        """Establish bidirectional Live API connection with Gemini, supporting fallback and backoff."""
        if not self.api_key or not self.api_key.strip() or self.api_key.startswith("your_"):
            raise ValueError(
                "GEMINI_API_KEY is not set or contains a placeholder. "
                "Please configure a valid GEMINI_API_KEY in backend/.env"
            )

        voice = resolve_live_voice_name(voice_name or DEFAULT_LIVE_VOICE)
        instruction = system_instruction or settings.default_system_instruction
        self._voice_name = voice
        self._system_instruction = instruction

        try:
            sdk_version = version("google-genai")
        except PackageNotFoundError:
            sdk_version = "unknown"
        logger.info("Initializing Gemini Live connection (google-genai=%s)", sdk_version)

        # Build LiveConnectConfig with native audio modalities & transcription.
        live_config = build_live_connect_config(instruction, voice)

        # Candidate API versions: v1beta is required for Live API BidiGenerateContent
        preferred_api_version = getattr(settings, "gemini_api_version", "v1beta") or "v1beta"
        candidate_api_versions: List[str] = [preferred_api_version]
        for v in ["v1beta", "v1alpha"]:
            if v not in candidate_api_versions:
                candidate_api_versions.append(v)

        # Candidate models to try in order
        candidate_models: List[str] = []
        if self.model_id:
            candidate_models.append(self.model_id)
        for fallback in self.FALLBACK_MODELS:
            if fallback not in candidate_models:
                candidate_models.append(fallback)

        last_error: Optional[Exception] = None

        for api_version in candidate_api_versions:
            logger.info("Configuring GenAI client with api_version=%s", api_version)
            client = genai.Client(
                api_key=self.api_key,
                http_options=types.HttpOptions(api_version=api_version)
            )

            for current_model in candidate_models:
                # Try up to 2 attempts per candidate with backoff on 503
                max_attempts = 2
                for attempt in range(max_attempts):
                    logger.info(
                        "Connecting to Gemini Live API with model=%s (api_version=%s, voice=%s, attempt %d/%d)",
                        current_model, api_version, voice, attempt + 1, max_attempts
                    )
                    try:
                        self._session_context = client.aio.live.connect(
                            model=current_model,
                            config=live_config
                        )
                        self._session = await self._session_context.__aenter__()
                        self._client = client
                        self._is_connected = True
                        self.model_id = current_model
                        logger.info(
                            "Connected successfully to Gemini Live session with model=%s (api_version=%s)",
                            current_model, api_version
                        )

                        # Spawn background listener for incoming model messages
                        self._receive_task = asyncio.create_task(self._receive_loop())

                        # Put connected signal
                        await self._event_queue.put(
                            ModelEvent(type=ModelEventType.CONNECTED, turn_id=self._current_turn_id)
                        )
                        return  # Successfully connected!

                    except Exception as e:
                        last_error = e
                        err_str = str(e)
                        is_transient = "503" in err_str or "UNAVAILABLE" in err_str or "high demand" in err_str or "429" in err_str
                        is_not_found = "404" in err_str or "Not Found" in err_str

                        logger.warning(
                            "Connection attempt to model %s (api_version=%s) failed (transient=%s, not_found=%s): %s%s",
                            current_model, api_version, is_transient, is_not_found, err_str, _upstream_rejection_details(e)
                        )

                        if self._session_context:
                            try:
                                await self._session_context.__aexit__(None, None, None)
                            except Exception:
                                pass
                            self._session = None
                            self._session_context = None

                        if is_transient and attempt + 1 < max_attempts:
                            backoff = 0.8 * (attempt + 1)
                            logger.info("Backing off for %.2fs before retrying %s...", backoff, current_model)
                            await asyncio.sleep(backoff)
                        else:
                            break  # Move to next candidate model

        # If all candidates and retries failed
        self._is_connected = False
        err_msg = str(last_error) if last_error else "Failed to establish Live session"
        if "503" in err_msg or "UNAVAILABLE" in err_msg or "high demand" in err_msg:
            friendly_msg = (
                "Gemini Live is currently experiencing a temporary capacity spike from Google servers (503 UNAVAILABLE). "
                "Please wait 5-10 seconds and click Connect again."
            )
            logger.error("All Live API models exhausted due to high Google capacity demand: %s", err_msg)
            raise RuntimeError(friendly_msg) from last_error
        elif "404" in err_msg or "Not Found" in err_msg:
            friendly_msg = (
                "Gemini Live API rejected the WebSocket connection (HTTP 404). "
                f"Attempted models {candidate_models} on API versions {candidate_api_versions}. "
                "Please verify that your GEMINI_API_KEY has access to the Gemini Live API in Google AI Studio."
            )
            logger.error("All Gemini Live candidates rejected with 404: %s", err_msg)
            raise RuntimeError(friendly_msg) from last_error
        else:
            logger.error("Failed to connect to any Gemini Live candidate: %s", err_msg, exc_info=True)
            raise last_error

    async def _receive_loop(self) -> None:
        """Continuously receive server messages from Gemini Live across multi-turn exchanges."""
        try:
            while self._is_connected and self._session is not None:
                try:
                    async for response in self._session.receive():
                        if not self._is_connected:
                            break

                        # 1. Handle ServerContent
                        server_content = response.server_content
                        if server_content is not None:
                            # Check for interruption
                            if getattr(server_content, "interrupted", False):
                                logger.info("Gemini Live detected user interruption.")
                                self._current_turn_id = str(uuid.uuid4())
                                await self._event_queue.put(
                                    ModelEvent(type=ModelEventType.INTERRUPTED, turn_id=self._current_turn_id)
                                )

                            # Check for input transcription (user's spoken speech)
                            input_tx = getattr(server_content, "input_transcription", None) or getattr(server_content, "interim_input_transcription", None)
                            if input_tx is not None and getattr(input_tx, "text", None):
                                await self._event_queue.put(
                                    ModelEvent(
                                        type=ModelEventType.TRANSCRIPT_INPUT,
                                        text=input_tx.text,
                                        is_final=bool(getattr(input_tx, "finished", False)),
                                        turn_id=self._current_turn_id
                                    )
                                )

                            # Check for output transcription (agent's spoken words transcription)
                            output_tx = getattr(server_content, "output_transcription", None)
                            if output_tx is not None and getattr(output_tx, "text", None):
                                await self._event_queue.put(
                                    ModelEvent(
                                        type=ModelEventType.TRANSCRIPT_OUTPUT,
                                        text=output_tx.text,
                                        is_final=bool(getattr(output_tx, "finished", False)),
                                        turn_id=self._current_turn_id
                                    )
                                )

                            # Check for model turn parts (audio and/or text)
                            model_turn = getattr(server_content, "model_turn", None)
                            if model_turn and getattr(model_turn, "parts", None):
                                for part in model_turn.parts:
                                    # Text part (if returned by model)
                                    if getattr(part, "text", None):
                                        await self._event_queue.put(
                                            ModelEvent(
                                                type=ModelEventType.TRANSCRIPT_OUTPUT,
                                                text=part.text,
                                                is_final=False,
                                                turn_id=self._current_turn_id
                                            )
                                        )
                                    # Audio chunk (inline_data with raw PCM 24kHz)
                                    inline_data = getattr(part, "inline_data", None)
                                    if inline_data and getattr(inline_data, "data", None):
                                        await self._event_queue.put(
                                            ModelEvent(
                                                type=ModelEventType.AUDIO_CHUNK,
                                                audio_bytes=inline_data.data,
                                                turn_id=self._current_turn_id
                                            )
                                        )

                            # Check if turn is complete
                            if getattr(server_content, "turn_complete", False):
                                await self._event_queue.put(
                                    ModelEvent(
                                        type=ModelEventType.TURN_COMPLETE,
                                        turn_id=self._current_turn_id
                                    )
                                )
                                # New turn ID for next exchange
                                self._current_turn_id = str(uuid.uuid4())
                except asyncio.CancelledError:
                    raise
                except Exception as inner_err:
                    if not self._is_connected or self._session is None:
                        break
                    raise inner_err

        except asyncio.CancelledError:
            logger.debug("Receive loop cancelled.")
        except Exception as e:
            err_str = str(e)
            if "503" in err_str or "UNAVAILABLE" in err_str or "high demand" in err_str:
                user_msg = (
                    "Gemini Live is temporarily experiencing high demand from Google. "
                    "Please wait a few seconds and try again."
                )
            elif "429" in err_str or "RESOURCE_EXHAUSTED" in err_str:
                user_msg = "Gemini API rate limit reached. Please wait a moment before sending more requests."
            else:
                user_msg = f"Live stream error: {err_str}"

            logger.error("Error in Gemini Live receive loop: %s", str(e), exc_info=True)
            await self._event_queue.put(
                ModelEvent(type=ModelEventType.ERROR, error_message=user_msg)
            )
        finally:
            self._is_connected = False

    async def ensure_connected(self) -> None:
        """Ensure session is connected, automatically reconnecting if needed."""
        if not self.is_connected or self._session is None:
            async with self._connect_lock:
                if not self.is_connected or self._session is None:
                    logger.info("Gemini Live session not connected; automatically reconnecting...")
                    await self.connect(
                        system_instruction=getattr(self, "_system_instruction", None),
                        voice_name=getattr(self, "_voice_name", None)
                    )

    async def send_audio_chunk(self, pcm_bytes: bytes) -> None:
        """Stream real-time audio chunk (16kHz PCM mono) to Gemini Live."""
        await self.ensure_connected()
        if not self.is_connected or not self._session:
            logger.warning("Cannot send audio chunk: session is not connected.")
            return

        blob = types.Blob(data=pcm_bytes, mime_type="audio/pcm;rate=16000")
        # Send PCM as audio explicitly. The generic `media` input is intended
        # for multimodal media chunks; the Live API audio path uses `audio`.
        await self._session.send_realtime_input(audio=blob)

    async def send_audio_end(self) -> None:
        """Signal end of audio stream."""
        if not self.is_connected or not self._session:
            return
        try:
            await self._session.send_realtime_input(audio_stream_end=True)
        except Exception as e:
            logger.warning("Failed to send audio_stream_end: %s", e)

    async def send_text(self, text: str, end_of_turn: bool = True) -> None:
        """Send typed user text message turn."""
        await self.ensure_connected()
        if not self.is_connected or not self._session:
            raise RuntimeError("Gemini Live session is not connected.")

        content = types.Content(
            role="user",
            parts=[types.Part.from_text(text=text)]
        )
        await self._session.send_client_content(turns=[content], turn_complete=end_of_turn)

    async def interrupt(self) -> None:
        """Notify session of interruption and drain local queues."""
        self._current_turn_id = str(uuid.uuid4())
        # Drain pending audio from queue
        while not self._event_queue.empty():
            try:
                self._event_queue.get_nowait()
            except asyncio.QueueEmpty:
                break

    async def stream_events(self) -> AsyncIterator[ModelEvent]:
        """Yield real-time events as they arrive from the model."""
        while not self._is_closed or not self._event_queue.empty():
            try:
                event = await asyncio.wait_for(self._event_queue.get(), timeout=0.1)
                yield event
            except asyncio.TimeoutError:
                continue

    async def disconnect(self) -> None:
        """Close connection cleanly and release resources."""
        self._is_closed = True
        self._is_connected = False
        if self._receive_task and not self._receive_task.done():
            self._receive_task.cancel()
            try:
                await self._receive_task
            except asyncio.CancelledError:
                pass
            self._receive_task = None

        if self._session_context:
            try:
                await self._session_context.__aexit__(None, None, None)
            except Exception as e:
                logger.warning("Error closing Gemini Live session: %s", e)
            self._session = None
            self._session_context = None

        self._client = None
        logger.info("Gemini Live session disconnected cleanly.")
