from typing import Optional

from .base import CamelModel, Field


class SettingsSchema(CamelModel):
    title1: Optional[str] = Field(description="Name of the site (1st part)")
    title2: Optional[str] = Field(description="Name of the site (2nd part)")
    about: Optional[str] = Field(description="Text to show in the about page (Markdown/HTML)")

    class Config:
        orm_mode = True
        schema_extra = {
            "example": {
                "title1": "Mono",
                "title2": "chrome",
                "about": "This is our about page",
            }
        }
