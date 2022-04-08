from typing import AsyncGenerator

from deta import Deta
from passlib.hash import bcrypt

from .config import get_settings
from .models import upload, user

db_settings = get_settings()


async def db_session() -> AsyncGenerator:
    yield Deta(db_settings.deta_project_key)


async def startup():
    """
    Removes lingering Upload sessions.
    Creates default user if first startup.
    """
    async for session in db_session():
        await upload.UploadSession.flush(session)

        init_db = session.AsyncBase("init")

        if not await init_db.get("initialized"):
            await init_db.put({"key": "initialized"})
            default_user = user.User(username="admin", hashed_password=bcrypt.hash("admin"))
            await default_user.save(session)

        await init_db.close()


async def shutdown():
    pass
