from datetime import datetime
from typing import ClassVar, Optional
from uuid import UUID

from deta import Deta
from fastapi_permissions import Allow, Everyone
from pydantic import Field

from .base import Base, NotFoundException
from .manga import Manga
from .progress import ProgressTracking


class ScanGroup(Base):
    id: str
    db_name: ClassVar = "scan_groups"


class Chapter(Base):
    name: str
    scan_group: str
    volume: Optional[int]
    number: float
    length: int
    webtoon: bool = False
    upload_time: datetime = Field(default_factory=datetime.now)

    owner_id: Optional[UUID]
    manga_id: UUID
    manga: Optional[Manga]

    db_name: ClassVar = "chapters"

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

    async def save(self, db_session: Deta):
        await ScanGroup(id=self.scan_group).save(db_session)
        await super().save(db_session)

    async def delete(self, db_session: Deta):
        from .comment import Comment
        from .progress import ProgressTracking
        from .upload import UploadSession

        chapters = await Comment._fetch(db_session, {"chapter_id": str(self.id)})
        tracking = await ProgressTracking._fetch(db_session, {"chapter_id": str(self.id)})
        sessions = await UploadSession._fetch(db_session, {"chapter_id": str(self.id)})

        for c in chapters:
            await c.delete(db_session)

        for p in tracking:
            await p.delete(db_session)

        for s in sessions:
            await s.delete(db_session)

        await super().delete(db_session)

    @classmethod
    async def find_detailed(cls, db_session: Deta, id: UUID, exception=NotFoundException):
        """
        Returns the chapter with the provided id, with the data of it's manga parent.
        """
        chapter = await Chapter.find(db_session, id, exception)
        manga = await Manga.find(db_session, chapter.manga_id, exception)
        return cls(**chapter.dict(exclude={"manga"}), manga=manga)

    @classmethod
    async def latest(cls, db_session: Deta, limit: int = 20, offset: int = 0, user_id: Optional[UUID] = None):
        count, page = await cls._pagination(db_session, {}, limit, offset, lambda x: x.upload_time, True)

        page = [chapter.dict() for chapter in page]

        cache = {}
        for chapter in page:
            if chapter["manga_id"] not in cache:
                cache[chapter["manga_id"]] = await Manga.find(db_session, chapter["manga_id"])
            chapter["manga"] = cache[chapter["manga_id"]]

        if user_id:
            page = [await ProgressTracking.from_chapter(db_session, result, user_id) for result in page]

        return count, page

    @classmethod
    async def from_manga(cls, db_session: Deta, manga_id: UUID, user_id: Optional[UUID] = None):
        query = {"manga_id": str(manga_id)}
        results = await cls._fetch(db_session, query)
        results = sorted(results, key=lambda x: x.number, reverse=True)

        if user_id:
            results = [await ProgressTracking.from_chapter(db_session, result, user_id) for result in results]

        return results

    @classmethod
    async def get_groups(cls, db_session: Deta):
        groups = await ScanGroup._fetch(db_session, {})
        return [group.id for group in groups]
