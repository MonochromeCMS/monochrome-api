from typing import ClassVar
from uuid import UUID

from deta import Deta
from fastapi_permissions import Allow, Authenticated

from .base import Base
from .chapter import Chapter


class ProgressTracking(Base):
    page: int
    read: bool
    chapter_version: int

    chapter_id: UUID
    author_id: UUID

    db_name: ClassVar = "progresstracking"

    @property
    def __acl__(self):
        return (
            *self.__class_acl__(),
            (Allow, [f"user:{self.author_id}"], "edit"),
            (Allow, [f"user:{self.author_id}"], "view"),
        )

    @classmethod
    def __class_acl__(cls):
        return (
            (Allow, [Authenticated], "create"),
            (Allow, ["role:uploader"], "view"),
            (Allow, ["role:admin"], "view"),
            (Allow, ["role:admin"], "edit"),
        )

    @classmethod
    async def get(cls, db_session: Deta, chapter_id: UUID, author_id: UUID):
        query = {
            "chapter_id": str(chapter_id),
            "author_id": str(author_id),
        }

        result = await cls._fetch(db_session, query)

        return result[0] if len(result) else None

    @classmethod
    async def from_chapter(cls, db_session: Deta, chapter: Chapter, author_id: UUID):
        """
        Returns the tracking progress for the current user on that chapter.
        """
        instance = await cls.get(db_session, chapter["id"], author_id)

        return {
            **chapter,
            "tracking": [instance] if instance else [],
        }
