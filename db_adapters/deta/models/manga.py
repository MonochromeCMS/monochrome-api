from datetime import datetime
from enum import Enum
from typing import ClassVar, Optional
from uuid import UUID

from deta import Deta
from fastapi_permissions import Allow, Everyone

from .base import Base, Field


class Status(str, Enum):
    ongoing = "ongoing"
    completed = "completed"
    hiatus = "hiatus"
    cancelled = "cancelled"


class Manga(Base):
    owner_id: Optional[UUID]
    title: str
    description: str
    author: str
    artist: str
    create_time: datetime = Field(default_factory=datetime.now)
    year: Optional[int] = Field(ge=1900, le=2100)
    status: Status

    db_name: ClassVar = "manga"

    @property
    def __acl__(self):
        return (
            *self.__class_acl__(),
            (Allow, ["role:uploader", f"user:{self.owner_id}"], "edit"),
        )

    @classmethod
    def __class_acl__(cls):
        return (
            (Allow, [Everyone], "view"),
            (Allow, ["role:admin"], "edit"),
            (Allow, ["role:admin"], "create"),
            (Allow, ["role:uploader"], "create"),
        )

    async def delete(self, db_session: Deta):
        from .chapter import Chapter
        from .upload import UploadSession

        sessions = await UploadSession._fetch(db_session, {"manga_id": str(self.id)})
        chapters = await Chapter._fetch(db_session, {"manga_id": str(self.id)})
        # Sessions need to be deleted first as deleting the chapters may delete some of them.
        for s in sessions:
            await s.delete(db_session)

        for c in chapters:
            await c.delete(db_session)

        await super().delete(db_session)

    @classmethod
    async def search(cls, db_session: Deta, title: str, limit: int = 20, offset: int = 0):
        """
        Returns a page of manga that fit the search query.
        """
        if title:
            query = {"title?contains": title}
        else:
            query = {}
        return await cls._pagination(db_session, query, limit, offset, lambda x: x.create_time)
