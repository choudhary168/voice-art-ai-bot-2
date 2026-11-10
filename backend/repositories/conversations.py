from sqlalchemy import select
from backend.database.models import Conversation

async def get_by_id(session, record_id):
    return await session.get(Conversation, record_id)

async def list_for_user(session, user_id):
    return (await session.scalars(select(Conversation).where(Conversation.user_id == user_id))).all()
