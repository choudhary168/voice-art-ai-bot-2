import asyncio
import logging
import time
import uuid
from typing import Callable, Coroutine, Optional
from backend.config import settings
from backend.providers.base import LiveModelProvider, ModelEvent, ModelEventType
from backend.schemas.events import (
    AudioChunkPayload,
    AudioEndPayload,
    LatencyMetrics,
    ResponseInterruptPayload,
    ServerAudioChunkPayload,
    ServerEvent,
    SessionStartPayload,
    TextMessagePayload,
)
from backend.services.audio import audio_service
from backend.services.knowledge import get_knowledge_provider

logger = logging.getLogger("orchestrator")


class SessionOrchestrator:
    """
    Coordinates client input, knowledge retrieval, and model event streaming.
    Ensures low latency by using asynchronous non-blocking pipelines and backpressure.
    """

    def __init__(
        self,
        session_id: str,
        provider: LiveModelProvider,
        send_to_client_callback: Callable[[ServerEvent], Coroutine]
    ):
        self.session_id = session_id
        self.provider = provider
        self.send_to_client = send_to_client_callback
        self.knowledge = get_knowledge_provider()

        # Audio sequencing and state
        self.current_turn_id: str = str(uuid.uuid4())
        self.audio_seq: int = 0
        self.is_active: bool = False
        self.response_started: bool = False

        # Monotonic latency tracking
        self.metrics = LatencyMetrics()
        self._provider_pump_task: Optional[asyncio.Task] = None
        self._audio_forward_error_reported = False

    async def start(self, start_payload: Optional[SessionStartPayload] = None) -> None:
        """Start session and establish live provider connection."""
        self.is_active = True
        self.metrics.client_session_start = start_payload.client_timestamp if start_payload else time.time()

        # Prepare system instruction enriched with knowledge context
        instruction = (start_payload.system_instruction if start_payload and start_payload.system_instruction else settings.default_system_instruction)
        voice = (start_payload.voice_name if start_payload and start_payload.voice_name else settings.voice_name)

        # Retrieve initial knowledge context (e.g. website overview or system seed)
        knowledge_res = await self.knowledge.retrieve_context(query="system overview")
        if knowledge_res.has_content():
            instruction += f"\n\nContext Information:\n{knowledge_res.format_for_system_instruction()}"

        try:
            # Connect model provider (supports automatic retry and fallback)
            await self.provider.connect(system_instruction=instruction, voice_name=voice)
            self.metrics.gemini_connected = time.time()

            # Send session.ready event
            await self.send_to_client(
                ServerEvent.session_ready(
                    session_id=self.session_id,
                    model=getattr(self.provider, "model_id", settings.gemini_model),
                    voice=voice,
                    input_sample_rate=settings.input_sample_rate,
                    output_sample_rate=settings.output_sample_rate,
                )
            )

            # Start continuous streaming event pump from provider to client
            self._provider_pump_task = asyncio.create_task(self._pump_provider_events())
        except Exception as e:
            self.is_active = False
            logger.error("Failed to establish session: %s", e)
            await self.send_to_client(
                ServerEvent.error(
                    code="UNAVAILABLE" if ("503" in str(e) or "UNAVAILABLE" in str(e)) else "SESSION_START_FAILED",
                    message=str(e),
                    recoverable=True
                )
            )

    async def handle_audio_chunk(self, chunk: AudioChunkPayload) -> None:
        """Process incoming raw audio chunk from microphone."""
        if not self.is_active:
            return

        if self.metrics.first_input_sent is None:
            self.metrics.first_input_sent = time.time()

        try:
            pcm_bytes = audio_service.decode_base64_pcm(chunk.data)
            # If client sent different sample rate, resample to 16kHz
            if chunk.sample_rate != 16000:
                pcm_bytes = audio_service.resample_linear(pcm_bytes, chunk.sample_rate, 16000)

            self._audio_chunk_count = getattr(self, "_audio_chunk_count", 0) + 1
            if self._audio_chunk_count == 1 or self._audio_chunk_count % 30 == 0:
                logger.info(
                    "Streaming microphone audio chunk #%d (%d bytes PCM, RMS level) to Gemini Live",
                    self._audio_chunk_count, len(pcm_bytes)
                )

            # Stream directly to model
            await self.provider.send_audio_chunk(pcm_bytes)
        except Exception as e:
            logger.error("Failed to forward audio chunk to provider: %s", e)
            # Surface the first failure in the UI without flooding it for every
            # subsequent microphone frame while the provider is unavailable.
            if not self._audio_forward_error_reported:
                self._audio_forward_error_reported = True
                await self.send_to_client(
                    ServerEvent.error(
                        code="AUDIO_SEND_ERROR",
                        message=f"Could not send microphone audio to Gemini Live: {e}",
                        recoverable=True,
                    )
                )

    async def handle_audio_end(self, end_payload: AudioEndPayload) -> None:
        """Process end of speech turn."""
        if not self.is_active:
            return
        logger.info("Received audio.end from client; signaling audio_stream_end to Gemini Live")
        await self.provider.send_audio_end()

    async def handle_text_message(self, text_payload: TextMessagePayload) -> None:
        """Process typed user text message."""
        if not self.is_active:
            return

        now = time.time()
        self._reset_turn_metrics(now)
        self.metrics.first_input_sent = now

        # Future knowledge retrieval hook: query specific context
        knowledge_res = await self.knowledge.retrieve_context(query=text_payload.text)
        prompt_text = text_payload.text
        if knowledge_res.has_content():
            prompt_text = (
                f"[Context Reference]\n{knowledge_res.format_for_system_instruction()}\n\n"
                f"[User Question]\n{text_payload.text}"
            )

        # Send text to model provider
        try:
            await self.provider.send_text(prompt_text, end_of_turn=True)
        except Exception as e:
            logger.error("Failed to forward text message to provider: %s", e)
            await self.send_to_client(
                ServerEvent.error(
                    code="UNAVAILABLE" if ("503" in str(e) or "UNAVAILABLE" in str(e)) else "SEND_ERROR",
                    message=(
                        "Gemini Live is currently experiencing a capacity spike (503). "
                        "Please wait a few seconds and try asking again."
                        if ("503" in str(e) or "UNAVAILABLE" in str(e))
                        else str(e)
                    ),
                    recoverable=True
                )
            )

    async def handle_interrupt(self, interrupt_payload: ResponseInterruptPayload) -> None:
        """Handle user interruption of current response."""
        logger.info("Handling response interrupt for turn %s", self.current_turn_id)
        self.audio_seq = 0
        self.response_started = False
        await self.provider.interrupt()
        # Notify client to discard audio playback buffer
        self.current_turn_id = str(uuid.uuid4())

    def _reset_turn_metrics(self, timestamp: float) -> None:
        """Reset turn-level metrics for fresh calculation."""
        self.metrics.first_input_sent = timestamp
        self.metrics.first_input_transcription = None
        self.metrics.first_model_response = None
        self.metrics.first_output_transcription = None
        self.metrics.first_audio_chunk = None
        self.metrics.turn_completed = None
        self.metrics.e2e_first_audio_ms = None
        self.metrics.e2e_first_transcription_ms = None
        self.metrics.total_turn_duration_ms = None
        self.response_started = False
        self.audio_seq = 0

    async def _pump_provider_events(self) -> None:
        """Read events from model provider and dispatch formatted ServerEvents to client."""
        try:
            async for event in self.provider.stream_events():
                if not self.is_active:
                    break

                now = time.time()

                if event.type == ModelEventType.CONNECTED:
                    logger.debug("Provider connected signal received.")

                elif event.type == ModelEventType.INTERRUPTED:
                    logger.info("Model event interrupted received.")
                    self.current_turn_id = event.turn_id or str(uuid.uuid4())
                    self.audio_seq = 0
                    self.response_started = False

                elif event.type == ModelEventType.TRANSCRIPT_INPUT:
                    if self.metrics.first_input_transcription is None:
                        self.metrics.first_input_transcription = now
                    await self.send_to_client(
                        ServerEvent.transcript_input(text=event.text or "", is_final=event.is_final)
                    )

                elif event.type == ModelEventType.TRANSCRIPT_OUTPUT:
                    if not self.response_started:
                        self.response_started = True
                        self.current_turn_id = event.turn_id or self.current_turn_id
                        await self.send_to_client(ServerEvent.response_started(turn_id=self.current_turn_id))

                    if self.metrics.first_model_response is None:
                        self.metrics.first_model_response = now
                    if self.metrics.first_output_transcription is None:
                        self.metrics.first_output_transcription = now
                        if self.metrics.first_input_sent:
                            self.metrics.e2e_first_transcription_ms = round(
                                (now - self.metrics.first_input_sent) * 1000, 2
                            )

                    await self.send_to_client(
                        ServerEvent.transcript_output(
                            text=event.text or "",
                            turn_id=self.current_turn_id,
                            is_final=event.is_final
                        )
                    )

                elif event.type == ModelEventType.AUDIO_CHUNK:
                    if not self.response_started:
                        self.response_started = True
                        self.current_turn_id = event.turn_id or self.current_turn_id
                        await self.send_to_client(ServerEvent.response_started(turn_id=self.current_turn_id))

                    if self.metrics.first_model_response is None:
                        self.metrics.first_model_response = now
                    if self.metrics.first_audio_chunk is None:
                        self.metrics.first_audio_chunk = now
                        if self.metrics.first_input_sent:
                            self.metrics.e2e_first_audio_ms = round(
                                (now - self.metrics.first_input_sent) * 1000, 2
                            )

                    if event.audio_bytes:
                        b64_audio = audio_service.encode_pcm_base64(event.audio_bytes)
                        self.audio_seq += 1
                        await self.send_to_client(
                            ServerEvent.audio_chunk(
                                data=b64_audio,
                                seq=self.audio_seq,
                                turn_id=self.current_turn_id,
                                sample_rate=settings.output_sample_rate
                            )
                        )

                elif event.type == ModelEventType.TURN_COMPLETE:
                    self.metrics.turn_completed = now
                    if self.metrics.first_input_sent:
                        self.metrics.total_turn_duration_ms = round(
                            (now - self.metrics.first_input_sent) * 1000, 2
                        )
                    await self.send_to_client(
                        ServerEvent.response_completed(
                            turn_id=self.current_turn_id,
                            metrics=self.metrics
                        )
                    )
                    # Prepare for next turn
                    self.response_started = False
                    self.audio_seq = 0
                    self.current_turn_id = str(uuid.uuid4())

                elif event.type == ModelEventType.ERROR:
                    logger.error("Model provider error event: %s", event.error_message)
                    await self.send_to_client(
                        ServerEvent.error(
                            code="PROVIDER_ERROR",
                            message=event.error_message or "An error occurred with the AI provider.",
                            recoverable=True
                        )
                    )

        except asyncio.CancelledError:
            logger.debug("Provider pump cancelled.")
        except Exception as e:
            logger.error("Error in provider pump loop: %s", e, exc_info=True)
            await self.send_to_client(
                ServerEvent.error(code="ORCHESTRATOR_ERROR", message=str(e), recoverable=False)
            )

    async def close(self, reason: str = "normal_closure") -> None:
        """Close orchestrator and clean up all provider resources."""
        self.is_active = False
        if self._provider_pump_task and not self._provider_pump_task.done():
            self._provider_pump_task.cancel()
            try:
                await self._provider_pump_task
            except asyncio.CancelledError:
                pass
            self._provider_pump_task = None

        await self.provider.disconnect()
        logger.info("Session %s closed cleanly. Reason: %s", self.session_id, reason)
