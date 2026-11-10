from backend.database.connection import SessionFactory


async def get_db_session():
    async with SessionFactory() as session:
        yield session
