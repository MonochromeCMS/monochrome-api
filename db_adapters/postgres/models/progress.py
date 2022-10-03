import uuid

from fastapi_permissions import Allow, Authenticated
from sqlalchemy import Boolean, Column, ForeignKey, Integer, and_, select
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.ext.asyncio import AsyncSession

from .base import Base


class ProgressTracking(Base):
    # Page allows us to return to the latest page read
    # TODO: decide if this should be synced to server or just sync the others, or make it opt-in
    page = Column(Integer, default=0, nullable=False)
    # Read allows us to show if a chapter has been read or not
    read = Column(Boolean, default=False, nullable=False)
    # Version allows us to tell the user if a read chapter has had an update
    chapter_version = Column(Integer, default=1, nullable=False)
    chapter_id = Column(UUID(as_uuid=True), ForeignKey("chapter.id", ondelete="CASCADE"), nullable=False)
    author_id = Column(UUID(as_uuid=True), ForeignKey("user.id", ondelete="CASCADE"), nullable=False)

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
    async def get(cls, db_session: AsyncSession, chapter_id: uuid.UUID, author_id: uuid.UUID):
        stmt = select(cls).where(and_(cls.chapter_id == chapter_id, cls.author_id == author_id))
        result = await db_session.execute(stmt)
        instance = result.scalars().first()

        return instance

    @classmethod
    async def from_chapter(cls, db_session: AsyncSession, chapter, author_id: uuid.UUID):
        """
        Returns the tracking progress for the current user on that chapter.
        """
        instance = await cls.get(db_session, chapter.id, author_id)

        return {
            **chapter.__dict__,
            "tracking": instance,
        }
