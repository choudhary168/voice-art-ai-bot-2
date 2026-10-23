import asyncio
import json
import logging
from typing import Optional
from fastapi import APIRouter, WebSocket, WebSocketDisconnect
from pydantic import ValidationError

from backend.config import settings
from backend.core.session_manager import session_manager
from backend.schemas.events import (
    AudioChunkPayload,
    AudioEndPayload,
    ClientEvent,
    ClientEventType,
    ResponseInterruptPayload,
    ServerEvent,
    SessionStartPayload,
    SessionStopPayload,
    TextMessagePayload,
)

logger = logging.getLogger("websocket_api")
router = APIRouter()


@router.websocket("/ws/live")
async def websocket_live_endpoint(websocket: WebSocket):
    """
    Bidirectional WebSocket endpoint for real-time voice and text agent conversation.
    """
    await websocket.accept()
    orchestrator = None
    ws_lock = asyncio.Lock()

    async def send_to_client(event: ServerEvent) -> None:
        """Deliver server event directly to WebSocket client with lock protection."""
        try:
            payload_str = json.dumps(event.model_dump())
            async with ws_lock:
                await websocket.send_text(payload_str)
        except Exception as e:
            logger.debug("Failed sending event to client: %s", e)

    try:
        # Create session
        orchestrator = await session_manager.create_session(send_to_client_callback=send_to_client)
        session_id = orchestrator.session_id
        logger.info("Client connected to /ws/live. Session: %s", session_id)

        # Inbound message loop
        while True:
            raw_text = await websocket.receive_text()

            # Enforce message size limit
            if len(raw_text) > settings.max_ws_message_size_bytes:
                await send_to_client(
                    ServerEvent.error(
                        code="MESSAGE_TOO_LARGE",
                        message=f"Payload exceeds limit of {settings.max_ws_message_size_bytes} bytes",
                        recoverable=True
                    )
                )
                continue

            try:
                data = json.loads(raw_text)
                event = ClientEvent.model_validate(data)
            except (json.JSONDecodeError, ValidationError) as e:
                logger.warning("Invalid event payload received: %s", e)
                await send_to_client(
                    ServerEvent.error(
                        code="INVALID_PAYLOAD",
                        message=f"Malformed event JSON or schema: {str(e)}",
                        recoverable=True
                    )
                )
                continue

            # Route client event
            if event.type == ClientEventType.SESSION_START:
                start_payload = SessionStartPayload.model_validate(event.payload)
                await orchestrator.start(start_payload)

            elif event.type == ClientEventType.AUDIO_CHUNK:
                chunk_payload = AudioChunkPayload.model_validate(event.payload)
                await orchestrator.handle_audio_chunk(chunk_payload)

            elif event.type == ClientEventType.AUDIO_END:
                end_payload = AudioEndPayload.model_validate(event.payload)
                await orchestrator.handle_audio_end(end_payload)

            elif event.type == ClientEventType.TEXT_MESSAGE:
                text_payload = TextMessagePayload.model_validate(event.payload)
                await orchestrator.handle_text_message(text_payload)

            elif event.type == ClientEventType.RESPONSE_INTERRUPT:
                interrupt_payload = ResponseInterruptPayload.model_validate(event.payload)
                await orchestrator.handle_interrupt(interrupt_payload)

            elif event.type == ClientEventType.SESSION_STOP:
                stop_payload = SessionStopPayload.model_validate(event.payload)
                await send_to_client(ServerEvent.closed(reason=stop_payload.reason or "user_stopped"))
                break

    except WebSocketDisconnect:
        logger.info("WebSocket disconnected normally by client.")
    except Exception as e:
        logger.error("Unhandled exception in WebSocket handler: %s", e, exc_info=True)
    finally:
        if orchestrator:
            await session_manager.remove_session(orchestrator.session_id, reason="websocket_closed")
            logger.info("Cleaned up session %s on disconnect.", orchestrator.session_id)
