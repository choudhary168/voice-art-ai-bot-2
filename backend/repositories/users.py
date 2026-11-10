from sqlalchemy import select
from backend.database.models import User

async def get_by_id(session, record_id):
    return await session.get(User, record_id)

async def list_for_user(session, user_id):
    return (await session.scalars(select(User).where(User.id == user_id))).all()
