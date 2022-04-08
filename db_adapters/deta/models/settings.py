from typing import ClassVar, Optional

from fastapi_permissions import Allow, Everyone

from .base import Base


class Settings(Base):
    id: str = "settings"
    title1: Optional[str]
    title2: Optional[str]
    about: Optional[str]

    db_name: ClassVar = "settings"

    __acl__ = (
        (Allow, [Everyone], "view"),
        (Allow, ["role:admin"], "edit"),
    )

    @classmethod
    async def set(cls, db_session, **kwargs):
        await cls(**kwargs).save(db_session)

    @classmethod
    async def get(cls, db_session):
        return await cls.find(db_session, "settings", None) or cls()
