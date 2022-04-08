import enum
import uuid
from typing import Optional, Union

from fastapi_permissions import Allow, Everyone
from pydantic import BaseModel
from sqlalchemy import Column, Enum, String, and_, select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import relationship

from .base import Base


class Role(str, enum.Enum):
    admin = "admin"
    uploader = "uploader"
    user = "user"


class User(Base):
    role = Column(Enum(Role), nullable=False, default=Role.user)
    username = Column(String(15), nullable=False, unique=True)
    email = Column(String, nullable=True)
    hashed_password = Column(String, nullable=False)

    # Delete all the related comments with the user.
    comments = relationship("Comment", back_populates="author", cascade="all, delete", passive_deletes=True)

    @property
    def principals(self):
        return [f"user:{self.id}", f"role:{self.role}"]

    @property
    def __acl__(self):
        return (
            *self.__class_acl__(),
            (Allow, [f"user:{self.id}"], "view"),
            (Allow, [f"user:{self.id}"], "edit"),
        )

    @classmethod
    def __class_acl__(cls):
        return (
            (Allow, [Everyone], "register"),
            (Allow, ["role:admin"], "create"),
            (Allow, ["role:admin"], "view"),
            (Allow, ["role:admin"], "edit"),
        )

    @classmethod
    async def from_username(cls, db_session: AsyncSession, username: str, ignore_user: uuid.UUID = None):
        stmt = select(cls).where(cls.username == username)

        if ignore_user:
            stmt = stmt.where(cls.id != ignore_user)

        result = await db_session.execute(stmt)
        return result.scalars().first()

    @classmethod
    async def from_email(cls, db_session: AsyncSession, email: Optional[str], ignore_user: uuid.UUID = None):
        if not email:
            return None

        stmt = select(cls).where(cls.email == email)

        if ignore_user:
            stmt = stmt.where(cls.id != ignore_user)

        result = await db_session.execute(stmt)
        return result.scalars().first()

    @classmethod
    async def from_username_email(cls, db_session: AsyncSession, user: str, ignore_user: uuid.UUID = None):
        """
        Return the user whose email/username matches the request, email takes priority
        """
        email_user = await cls.from_email(db_session, user, ignore_user)
        username_user = await cls.from_username(db_session, user, ignore_user)

        return email_user or username_user

    @classmethod
    async def search(
        cls,
        db_session: AsyncSession,
        name: str = "",
        filters: Union[BaseModel, None] = None,
        limit: int = 20,
        offset: int = 0,
    ):
        """
        Returns a page of users fitting the criteria.
        """
        stmt = select(cls).where(cls.username.ilike(f"%{name}%"))
        if filters is not None:
            filters = {k: v for k, v in filters.dict().items() if v}
            stmt = stmt.where(and_(True, *[getattr(cls, k) == v for k, v in filters.items()]))
        return await cls._pagination(db_session, stmt, limit, offset, (cls.username,))
