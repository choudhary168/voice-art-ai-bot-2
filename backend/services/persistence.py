"""Bounded, best-effort persistence worker; producers never perform SQL."""
import asyncio
import logging
import uuid
from dataclasses import dataclass
from typing import Any
from sqlalchemy import select
from sqlalchemy.dialects.postgresql import insert
from backend.config import settings
from backend.database.connection import SessionFactory
from backend.database.models import Message

logger = logging.getLogger(__name__)


@dataclass
class PersistEvent:
    kind: str
    data: dict[str, Any]


class PersistenceQueue:
    def __init__(self):
        self.queue: asyncio.Queue[PersistEvent] = asyncio.Queue(settings.persistence_queue_capacity)
        self.worker: asyncio.Task | None = None
        self.accepting = False
        self.dropped = 0
        self.failed = 0

    def start(self):
        if settings.database_enabled and (self.worker is None or self.worker.done()):
            self.accepting = True
            self.worker = asyncio.create_task(self._run())

    def enqueue(self, kind: str, **data: Any) -> bool:
        if not self.accepting:
            return False
        try:
            self.queue.put_nowait(PersistEvent(kind, data))
            return True
        except asyncio.QueueFull:
            self.dropped += 1
            logger.error("Persistence queue full; event dropped (kind=%s, dropped=%d)", kind, self.dropped)
            return False

    async def _write(self, event: PersistEvent):
        async with SessionFactory() as session:
            if event.kind == "message":
                values = dict(event.data)
                values["conversation_id"] = uuid.UUID(str(values["conversation_id"]))
                values["user_id"] = uuid.UUID(str(values["user_id"]))
                stmt = insert(Message).values(**values).on_conflict_do_nothing(constraint="uq_message_turn_role")
                await session.execute(stmt)
            elif event.kind == "conversation_end":
                from backend.database.models import Conversation
                from sqlalchemy import update
                await session.execute(update(Conversation).where(Conversation.id == uuid.UUID(str(event.data["id"]))).values(status="completed", ended_at=event.data["ended_at"]))
            elif event.kind == "analytics":
                from backend.database.models import AnalyticsEvent
                values = dict(event.data)
                values["user_id"] = uuid.UUID(str(values["user_id"])) if values.get("user_id") else None
                values["conversation_id"] = uuid.UUID(str(values["conversation_id"])) if values.get("conversation_id") else None
                session.add(AnalyticsEvent(**values))
            elif event.kind == "conversation_start":
                from backend.database.models import User, Conversation
                user_id = uuid.UUID(str(event.data["user_id"]))
                conversation_id = uuid.UUID(str(event.data["conversation_id"]))
                session.add(User(id=user_id, identity_type="anonymous", status="active"))
                session.add(Conversation(id=conversation_id, user_id=user_id, status="active"))
            await session.commit()

    async def _run(self):
        while self.accepting or not self.queue.empty():
            try:
                event = await asyncio.wait_for(self.queue.get(), timeout=0.2)
            except asyncio.TimeoutError:
                continue
            try:
                for attempt in range(settings.persistence_retry_attempts + 1):
                    try:
                        await self._write(event)
                        break
                    except Exception:
                        if attempt == settings.persistence_retry_attempts:
                            self.failed += 1
                            logger.exception("Persistence event failed (kind=%s, failed=%d)", event.kind, self.failed)
                        else:
                            await asyncio.sleep(min(0.1 * (2 ** attempt), 1.0))
            finally:
                self.queue.task_done()

    async def stop(self):
        self.accepting = False
        if self.worker:
            try:
                await asyncio.wait_for(self.worker, settings.persistence_shutdown_timeout)
            except asyncio.TimeoutError:
                logger.error("Persistence queue drain timed out; remaining=%d", self.queue.qsize())
                self.worker.cancel()
                await asyncio.gather(self.worker, return_exceptions=True)
            self.worker = None


persistence_queue = PersistenceQueue()
