import uuid

from fastapi_permissions import Allow
from sqlalchemy import Column, ForeignKey, String, delete, select
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import joinedload, relationship

from .base import Base, NotFoundException


class UploadSession(Base):
    owner_id = Column(UUID(as_uuid=True), ForeignKey("user.id", name="fk_session_owner", ondelete="CASCADE"))

    manga_id = Column(UUID(as_uuid=True), ForeignKey("manga.id", ondelete="CASCADE"), nullable=False)
    manga = relationship("Manga", back_populates="sessions")
    chapter_id = Column(UUID(as_uuid=True), ForeignKey("chapter.id", ondelete="CASCADE"))
    chapter = relationship("Chapter", back_populates="sessions")

    # Related blobs are deleted with the session
    blobs = relationship("UploadedBlob", back_populates="session", cascade="all, delete", passive_deletes=True)

    @property
    def __acl__(self):
        return (
            *self.__class_acl__(),
            (Allow, ["role:uploader", f"user:{self.owner_id}"], "view"),
            (Allow, ["role:uploader", f"user:{self.owner_id}"], "edit"),
        )

    @classmethod
    def __class_acl__(cls):
        return (
            (Allow, ["role:admin"], "create"),
            (Allow, ["role:uploader"], "create"),
            (Allow, ["role:admin"], "view"),
            (Allow, ["role:admin"], "edit"),
        )

    @classmethod
    async def find_detailed(cls, db_session: AsyncSession, id: uuid.UUID, exception=NotFoundException):
        """
        Returns the requested upload session, with its related blobs.
        """
        stmt = select(cls).where(cls.id == id).options(joinedload(cls.blobs))
        result = await db_session.execute(stmt)
        instance = result.scalars().first()
        if instance is None:
            if exception:
                raise exception
            else:
                return None
        else:
            return instance

    @classmethod
    async def flush(cls, db_session: AsyncSession):
        """
        Delete all the upload sessions.
        """
        stmt = delete(cls)

        return await db_session.execute(stmt)


class UploadedBlob(Base):
    name = Column(String, nullable=False)

    session_id = Column(UUID(as_uuid=True), ForeignKey("uploadsession.id", ondelete="CASCADE"), nullable=False)
    session = relationship("UploadSession", back_populates="blobs")

    @classmethod
    async def from_session(cls, db_session: AsyncSession, session_id: UUID):
        """
        Returns all the blobs from the provided upload session.
        """
        stmt = select(cls).where(cls.session_id == session_id)
        result = await db_session.execute(stmt)

        return result.scalars().all()
