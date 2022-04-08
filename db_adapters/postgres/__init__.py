from .models import upload
from .session import db_session, engine

db_session = db_session


async def startup():
    """
    Removes lingering Upload sessions.
    """
    async for session in db_session():
        await upload.UploadSession.flush(session)


async def shutdown():
    """
    Disconnects from the database.
    """
    await engine.dispose()
