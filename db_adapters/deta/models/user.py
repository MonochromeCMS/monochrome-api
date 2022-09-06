from datetime import datetime
from enum import Enum
from typing import ClassVar, Optional, Union
from uuid import UUID

from deta import Deta
from fastapi_permissions import Allow, Everyone
from pydantic import BaseModel, EmailStr, Field

from .base import Base


class Role(str, Enum):
    admin = "admin"
    uploader = "uploader"
    user = "user"


class User(Base):
    role: Role = Role.admin
    username: str
    email: Optional[EmailStr]
    hashed_password: str
    update_time: datetime = Field(default_factory=datetime.now)

    db_name: ClassVar = "users"

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

    async def save(self, db_session: Deta):
        """
        Overrides the default save method to update the update_time.
        """
        self.update_time = datetime.now()
        await super().save(db_session)

    async def delete(self, db_session: Deta):
        from .comment import Comment
        from .progress import ProgressTracking

        comments = await Comment._fetch(db_session, {"author_id": str(self.id)})
        tracking = await ProgressTracking._fetch(db_session, {"author_id": str(self.id)})

        for c in comments:
            await c.delete(db_session)

        for p in tracking:
            await p.delete(db_session)
        await super().delete(db_session)

    @classmethod
    async def from_username(cls, db_session: Deta, username: str, ignore_user: UUID = None):
        query = {"username": username}

        if ignore_user:
            query["id,ne"] = str(ignore_user)

        result = await cls._fetch(db_session, query)

        return result[0] if result else None

    @classmethod
    async def from_email(cls, db_session: Deta, email: Optional[str], ignore_user: UUID = None):
        if not email:
            return None

        query = {"email": email}

        if ignore_user:
            query["id,ne"] = str(ignore_user)

        result = await cls._fetch(db_session, query)

        return result[0] if result else None

    @classmethod
    async def from_username_email(cls, db_session: Deta, user: str, ignore_user: UUID = None):
        """
        Return the user whose email/username matches the request, email takes priority
        """
        email_user = await cls.from_email(db_session, user, ignore_user)
        username_user = await cls.from_username(db_session, user, ignore_user)

        return email_user or username_user

    @classmethod
    async def search(
        cls, db_session: Deta, name: str = "", filters: Union[BaseModel, None] = None, limit: int = 20, offset: int = 0
    ):
        if filters is not None:
            filters = {k: v for k, v in filters.dict().items() if v}
        else:
            filters = {}
        if name:
            filters["username?contains"] = name
        return await cls._pagination(db_session, filters, limit, offset, lambda x: getattr(x, "username"))
