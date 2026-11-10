from sqlalchemy import select
from backend.database.models import Message

async def get_by_id(session, record_id):
    return await session.get(Message, record_id)

async def list_for_user(session, user_id):
    return (await session.scalars(select(Message).where(Message.user_id == user_id))).all()
