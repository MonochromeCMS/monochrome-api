from datetime import datetime
from typing import Optional
from uuid import UUID

from ..db import models
from .base import CamelModel, Field, PaginationResponse


class MangaSchema(CamelModel):
    title: str = Field(description="Title of the manga")
    description: str = Field(
        description="Short description of the manga",
    )
    author: str = Field(
        description="Author of the manga",
    )
    artist: str = Field(
        description="Artist of the manga",
    )
    year: Optional[int] = Field(
        description="Year of release of the manga",
    )
    status: models.manga.Status = Field(
        description="Status of the manga",
    )

    class Config:
        schema_extra = {
            "example": {
                "title": "Monochrome Lovers",
                "description": "One day, suddenly, an angel came descending from the sky!?",
                "author": "Hibiki Mio",
                "artist": "Hibiki Mio",
                "year": 2021,
                "status": models.manga.Status.ongoing,
            }
        }


class ShortMangaResponse(CamelModel):
    title: str = Field(description="Title of the manga")
    version: int = Field(
        description="Version of the manga",
    )


class MangaResponse(MangaSchema):
    id: UUID = Field(
        title="ID",
        description="ID of the manga",
    )
    version: int = Field(
        description="Version of the manga",
    )
    create_time: datetime = Field(
        description="Time this manga was created",
    )
    owner_id: Optional[UUID] = Field(description="User that created this manga")

    class Config:
        orm_mode = True
        schema_extra = {
            "example": {
                "id": "1e01d7f6-c4e1-4102-9dd0-a6fccc065978",
                "title": "Monochrome Lovers",
                "description": "One day, suddenly, an angel came descending from the sky!?",
                "author": "Hibiki Mio",
                "artist": "Hibiki Mio",
                "year": 2021,
                "status": models.manga.Status.ongoing,
                "version": 2,
                "createTime": "2000-08-24 00:00:00",
                "ownerId": "6901d7f6-c4e1-4200-9dd0-a6fccc065978",
            }
        }


class MangaSearchResponse(PaginationResponse):
    results: list[MangaResponse]
