from typing import ClassVar, List, Optional
from uuid import UUID

from deta import Deta
from fastapi_permissions import Allow

from .base import Base, NotFoundException


class UploadedBlob(Base):
    name: str

    session_id: UUID

    db_name: ClassVar = "blobs"

    @classmethod
    async def from_session(cls, db_session: Deta, session_id: UUID):
        """
        Returns all the blobs from the provided upload session.
        """
        return await UploadedBlob._fetch(db_session, {"session_id": str(session_id)})


class UploadSession(Base):
    owner_id: Optional[UUID]

    manga_id: UUID
    chapter_id: Optional[UUID]

    blobs: Optional[List[UploadedBlob]]

    db_name: ClassVar = "sessions"

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

    async def delete(self, db_session: Deta):
        blobs = await UploadedBlob._fetch(db_session, {"session_id": str(self.id)})

        for b in blobs:
            await b.delete(db_session)

        await super().delete(db_session)

    @classmethod
    async def find_detailed(cls, db_session: Deta, id: UUID, exception=NotFoundException):
        """
        Returns the requested upload session, with its related blobs.
        """
        session = await UploadSession.find(db_session, id, exception)
        blobs = await UploadedBlob._fetch(db_session, {"session_id": str(id)})
        return cls(**session.dict(exclude={"blobs"}), blobs=blobs)

    @classmethod
    async def flush(cls, db_session: Deta):
        """
        Delete all the upload sessions.
        """
        sessions = await cls._fetch(db_session, {})

        for s in sessions:
            await s.delete(db_session)
