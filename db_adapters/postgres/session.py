from typing import AsyncGenerator

from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine
from sqlalchemy.orm import sessionmaker

from .config import get_settings

db_settings = get_settings()

engine = create_async_engine(
    db_settings.url,
    future=True,
    # echo=True, # To debug SQL queries
)

# expire_on_commit=False will prevent attributes from being expired after commit.
async_session = sessionmaker(engine, expire_on_commit=False, class_=AsyncSession)


async def db_session() -> AsyncGenerator:
    """Returns the session as a FastAPI dependency (simply an async generator)"""
    session = async_session()
    try:
        yield session
        await session.commit()
    except SQLAlchemyError as ex:
        await session.rollback()
        raise ex
    finally:
        await session.close()
