import uuid

from fastapi_permissions import Allow, Everyone
from sqlalchemy import Boolean, Column, DateTime, Float, ForeignKey, Integer, String, func, select, or_
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import joinedload, relationship

from .base import Base, NotFoundException
from .progress import ProgressTracking
from .manga import Manga


class Chapter(Base):
    name = Column(String, nullable=False)
    scan_group = Column(String, nullable=False)
    volume = Column(Integer, nullable=True)
    number = Column(Float, nullable=False)
    length = Column(Integer, nullable=False)
    webtoon = Column(Boolean, default=False, nullable=False)
    upload_time = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)

    owner_id = Column(UUID(as_uuid=True), ForeignKey("user.id", name="fk_chapter_owner", ondelete="SET NULL"))
    manga_id = Column(UUID(as_uuid=True), ForeignKey("manga.id", ondelete="CASCADE"), nullable=False)
    manga = relationship("Manga", back_populates="chapters")

    # Related sessions, tracking and comments are deleted with the chapter
    sessions = relationship("UploadSession", back_populates="chapter", cascade="all, delete", passive_deletes=True)
    comments = relationship("Comment", back_populates="chapter", cascade="all, delete", passive_deletes=True)
    tracking = relationship("ProgressTracking", cascade="all, delete", passive_deletes=True)

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
        )

    @classmethod
    async def find_detailed(cls, db_session: AsyncSession, id: uuid.UUID, exception=NotFoundException):
        """
        Returns the chapter with the provided id, with the data of it's manga parent.
        """
        stmt = select(cls).where(cls.id == id).options(joinedload(cls.manga))
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
    async def latest(cls, db_session: AsyncSession, limit: int = 20, offset: int = 0, user_id: uuid.UUID = None):
        """
        Returns a page of the latest chapters uploaded, they also include the details of their related manga.
        """
        stmt = select(cls).outerjoin(cls.manga).options(joinedload(cls.manga))
        
        if user_id:
            stmt = stmt.outerjoin(cls.tracking).options(joinedload(cls.tracking)).where(or_(cls.tracking == None, ProgressTracking.author_id == user_id))
        
        print(str(stmt))
        return await cls._pagination(db_session, stmt, limit, offset, (cls.upload_time.desc(),))

    @classmethod
    async def from_manga(cls, db_session: AsyncSession, manga_id: uuid.UUID, user_id: uuid.UUID = None):
        """
        Returns all the chapters ordered by number that are related to the provided manga.
        """
        stmt = select(cls).where(cls.manga_id == manga_id).order_by(cls.number.desc())
        
        if user_id:
            stmt = stmt.options(joinedload(cls.tracking)).where(or_(cls.tracking == None, ProgressTracking.author_id == user_id))
        
        result = await db_session.execute(stmt)
        return result.unique().scalars().all()

    @classmethod
    async def get_groups(cls, db_session: AsyncSession):
        """
        Returns all the scan groups saved in the database (all the groups that have at least a chapter uploaded).
        """
        stmt = select(cls.scan_group).distinct()
        result = await db_session.execute(stmt)
        return result.scalars().all()
