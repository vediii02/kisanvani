from db.session import get_db

async def get_current_db():
    async for db in get_db():
        yield db