from typing import Optional
from uuid import UUID

from .base import CamelModel, Field
from .chapter import ChapterSchema


class UploadSessionSchema(CamelModel):
    manga_id: UUID = Field(
        description="Manga this session is linked to",
    )
    chapter_id: Optional[UUID] = Field(description="Chapter to edit, if in edition mode")

    class Config:
        schema_extra = {
            "example": {
                "mangaId": "1e01d7f6-c4e1-4102-9dd0-a6fccc065978",
                "chapterId": "116bdaa6-f62d-4b53-98b2-237adbaad788",
            }
        }


class UploadedBlobResponse(CamelModel):
    id: UUID = Field(
        description="ID of the uploaded blob",
    )
    name: str = Field(
        description="Name the blob was uploaded as",
    )

    class Config:
        orm_mode = True
        schema_extra = {
            "example": {
                "id": "eadec6fe-619f-4d7f-8328-f8a5563d3325",
                "name": "001.png",
            }
        }


class UploadSessionResponse(UploadSessionSchema):
    id: UUID = Field(
        description="ID of the upload session",
    )
    blobs: list[UploadedBlobResponse] = Field(
        [],
        description="Images uploaded to the session",
    )
    owner_id: Optional[UUID] = Field(description="User that created this upload session")

    class Config:
        orm_mode = True


class CommitUploadSession(CamelModel):
    chapter_draft: ChapterSchema = Field(description="Details of the chapter")
    page_order: list[UUID] = Field(description="Order the pages should be uploaded in")
