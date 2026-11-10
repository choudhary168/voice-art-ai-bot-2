from sqlalchemy import select
from backend.database.models import KnowledgeDocument

async def get_by_id(session, record_id):
    return await session.get(KnowledgeDocument, record_id)

async def list_for_user(session, user_id):
    return (await session.scalars(select(KnowledgeDocument).where(KnowledgeDocument.is_active.is_(True)))).all()
