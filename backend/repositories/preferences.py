from sqlalchemy import select
from backend.database.models import UserPreference

async def get_by_id(session, record_id):
    return await session.get(UserPreference, record_id)

async def list_for_user(session, user_id):
    return (await session.scalars(select(UserPreference).where(UserPreference.user_id == user_id))).all()
