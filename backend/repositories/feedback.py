from sqlalchemy import select
from backend.database.models import Feedback

async def get_by_id(session, record_id):
    return await session.get(Feedback, record_id)

async def list_for_user(session, user_id):
    return (await session.scalars(select(Feedback).where(Feedback.user_id == user_id))).all()
