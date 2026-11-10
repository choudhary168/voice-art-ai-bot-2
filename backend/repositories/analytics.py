from sqlalchemy import select
from backend.database.models import AnalyticsEvent

async def get_by_id(session, record_id):
    return await session.get(AnalyticsEvent, record_id)

async def list_for_user(session, user_id):
    return (await session.scalars(select(AnalyticsEvent).where(AnalyticsEvent.user_id == user_id))).all()
