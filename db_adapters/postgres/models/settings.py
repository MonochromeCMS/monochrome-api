from fastapi_permissions import Allow, Everyone
from sqlalchemy import Column, SmallInteger, Text, select
from sqlalchemy.ext.declarative import declarative_base

from .base import Base

BasicBase = declarative_base(metadata=Base.metadata)


class Settings(BasicBase):
    __tablename__ = "settings"

    id = Column(SmallInteger, primary_key=True)
    title1 = Column(Text, nullable=True)
    title2 = Column(Text, nullable=True)
    about = Column(Text, nullable=True)

    __acl__ = (
        (Allow, [Everyone], "view"),
        (Allow, ["role:admin"], "edit"),
    )

    @classmethod
    async def set(cls, db_session, **kwargs):
        instance = await cls.get(db_session)

        for k, v in kwargs.items():
            setattr(instance, k, v)

        db_session.add(instance)
        await db_session.commit()

        return instance

    @classmethod
    async def get(cls, db_session):
        stmt = select(cls).where(cls.id == 1)
        result = await db_session.execute(stmt)
        return result.scalars().first() or cls(id=1)
