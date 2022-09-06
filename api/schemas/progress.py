from uuid import UUID

from .base import CamelModel, Field


class ProgressTrackingSchema(CamelModel):
    chapter_id: UUID = Field(description="ID of the chapter")

    page: int = Field(description="Last page of the chapter read")
    read: bool = Field(description="Wether the chapter has been read")
    chapter_version: int = Field(description="The version of the chapter that was read")

    class Config:
        orm_mode = True
        schema_extra = {
            "example": {
                "chapterId": "4abe53f4-0eaa-4f31-9210-a625fa665e23",
                "page": 18,
                "read": False,
                "chapter_version": 1,
            }
        }
