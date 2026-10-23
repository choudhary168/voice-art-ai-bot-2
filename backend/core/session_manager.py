import asyncio
import logging
import uuid
from typing import Callable, Coroutine, Dict, Optional
from backend.config import settings
from backend.core.orchestrator import SessionOrchestrator
from backend.providers.base import LiveModelProvider
from backend.providers.gemini_live import GeminiLiveProvider
from backend.providers.mock_live import MockModelProvider
from backend.schemas.events import ServerEvent

logger = logging.getLogger("session_manager")


class SessionManager:
    """
    Manages active client sessions, provider instantiations, and graceful cleanup.
    """

    def __init__(self):
        self._sessions: Dict[str, SessionOrchestrator] = {}
        self._lock = asyncio.Lock()

    async def create_session(
        self,
        send_to_client_callback: Callable[[ServerEvent], Coroutine],
        session_id: Optional[str] = None,
        force_mock: bool = False
    ) -> SessionOrchestrator:
        """Create and register a new session orchestrator."""
        sid = session_id or str(uuid.uuid4())

        # Select provider based on configuration and availability
        provider: LiveModelProvider
        if force_mock:
            logger.info("Instantiating MockModelProvider for session %s", sid)
            provider = MockModelProvider()
        elif settings.has_api_key:
            logger.info("Instantiating GeminiLiveProvider for session %s with model %s", sid, settings.gemini_model)
            provider = GeminiLiveProvider(model_id=settings.gemini_model, api_key=settings.gemini_api_key)
        else:
            logger.warning(
                "GEMINI_API_KEY is not set or placeholder detected in environment. "
                "Falling back to MockModelProvider so session %s remains testable and responsive.",
                sid
            )
            provider = MockModelProvider()

        orchestrator = SessionOrchestrator(
            session_id=sid,
            provider=provider,
            send_to_client_callback=send_to_client_callback
        )

        async with self._lock:
            self._sessions[sid] = orchestrator

        logger.info("Created session %s (Total active sessions: %d)", sid, len(self._sessions))
        return orchestrator

    async def get_session(self, session_id: str) -> Optional[SessionOrchestrator]:
        async with self._lock:
            return self._sessions.get(session_id)

    async def remove_session(self, session_id: str, reason: str = "client_disconnected") -> None:
        """Close and remove an active session."""
        async with self._lock:
            orchestrator = self._sessions.pop(session_id, None)

        if orchestrator:
            try:
                await orchestrator.close(reason=reason)
            except Exception as e:
                logger.error("Error closing session %s: %s", session_id, e)
            logger.info("Removed session %s (Remaining active: %d)", session_id, len(self._sessions))

    async def cleanup_all(self) -> None:
        """Clean up all active sessions on shutdown."""
        async with self._lock:
            sessions_to_close = list(self._sessions.values())
            self._sessions.clear()

        for orchestrator in sessions_to_close:
            try:
                await orchestrator.close(reason="server_shutdown")
            except Exception as e:
                logger.error("Error shutting down session %s: %s", orchestrator.session_id, e)


# Global singleton
session_manager = SessionManager()
