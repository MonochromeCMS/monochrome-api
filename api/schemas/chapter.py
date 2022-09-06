from datetime import datetime
from typing import List, Optional
from uuid import UUID

from .base import CamelModel, Field, PaginationResponse
from .manga import ShortMangaResponse
from .progress import ProgressTrackingSchema


class ChapterSchema(CamelModel):
    name: str = Field(description="Name of the chapter")
    webtoon: bool = Field(description="If this chapter is a webtoon")
    volume: Optional[int] = Field(
        description="Volume this chapter comes from",
    )
    number: float = Field(description="Number of the chapter")
    scan_group: Optional[str] = Field("no group", description="Scanlation group publishing this chapter")

    class Config:
        schema_extra = {
            "example": {
                "name": "A World That Won't Reject Me",
                "webtoon": True,
                "volume": 1,
                "number": "19.5",
                "scanGroup": "Monochrome Scans",
            }
        }


class ChapterResponse(ChapterSchema):
    id: UUID = Field(
        title="ID",
        description="ID of the manga",
    )
    version: int = Field(
        description="Version of the chapter",
    )
    manga_id: UUID = Field(
        description="Manga this chapter comes from",
    )
    length: int = Field(
        description="Amount of pages of the chapter",
        ge=1,
    )
    upload_time: datetime = Field(
        description="Time this chapter was uploaded",
    )
    owner_id: Optional[UUID] = Field(description="User that uploaded this chapter")

    class Config:
        orm_mode = True
        schema_extra = {
            "example": {
                "name": "A World That Won't Reject Me",
                "webtoon": True,
                "volume": 1,
                "number": "19.5",
                "scanGroup": "Monochrome Scans",
                "id": "4abe53f4-0eaa-4f31-9210-a625fa665e23",
                "version": 2,
                "manga_id": "1e01d7f6-c4e1-4102-9dd0-a6fccc065978",
                "length": 15,
                "uploadTime": "2000-08-24 00:00:00",
                "ownerId": "6901d7f6-c4e1-4200-9dd0-a6fccc065978",
            }
        }


class DetailedChapterResponse(ChapterResponse):
    manga: ShortMangaResponse


class LatestChaptersResponse(PaginationResponse):
    results: List[DetailedChapterResponse]
