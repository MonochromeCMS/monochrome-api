from datetime import datetime
from typing import ClassVar, Optional
from uuid import UUID

from deta import Deta
from fastapi_permissions import Allow, Authenticated, Everyone
from pydantic import Field

from .base import Base
from .user import User


class Comment(Base):
    content: str
    reply_to: Optional[UUID]
    create_time: datetime = Field(default_factory=datetime.now)

    chapter_id: UUID
    author_id: UUID
    author: Optional[User]

    db_name: ClassVar = "comment"

    @property
    def __acl__(self):
        return (
            *self.__class_acl__(),
            (Allow, [f"user:{self.author_id}"], "edit"),
        )

    @classmethod
    def __class_acl__(cls):
        return (
            (Allow, [Everyone], "view"),
            (Allow, [Authenticated], "create"),
            (Allow, ["role:uploader"], "edit"),
            (Allow, ["role:admin"], "edit"),
        )

    @classmethod
    async def from_chapter(cls, db_session: Deta, chapter_id: UUID, limit: int = 20, offset: int = 0):
        query = {"chapter_id": str(chapter_id)}
        count, page = await Comment._pagination(db_session, query, limit, offset, lambda x: x.create_time)

        page = [comment.dict() for comment in page]

        cache = {}
        for comment in page:
            if comment["author_id"] not in cache:
                cache[comment["author_id"]] = await User.find(db_session, comment["author_id"])
            comment["author"] = cache[comment["author_id"]]

        return count, page
