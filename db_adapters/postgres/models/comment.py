import uuid

from fastapi_permissions import Allow, Authenticated, Everyone
from sqlalchemy import Column, DateTime, ForeignKey, String, func, select
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import joinedload, relationship

from .base import Base


class Comment(Base):
    content = Column(String, nullable=False)
    reply_to = Column(UUID(as_uuid=True))
    create_time = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)

    chapter_id = Column(UUID(as_uuid=True), ForeignKey("chapter.id", ondelete="CASCADE"), nullable=False)
    chapter = relationship("Chapter", back_populates="comments")
    author_id = Column(UUID(as_uuid=True), ForeignKey("user.id", ondelete="CASCADE"), nullable=False)
    author = relationship("User", back_populates="comments")

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
    async def from_chapter(
        cls,
        db_session: AsyncSession,
        chapter_id: uuid.UUID,
        limit: int = 20,
        offset: int = 0,
    ):
        """
        Returns a page of comments from the provided chapter.
        """
        stmt = select(cls).where(cls.chapter_id == chapter_id).options(joinedload(cls.author))
        return await cls._pagination(db_session, stmt, limit, offset, (cls.create_time.desc(),))
