from fastapi_camelcase import CamelModel
from pydantic import Field

from ..config import get_settings

global_settings = get_settings()


class PaginationResponse(CamelModel):
    offset: int = Field(..., ge=0)
    limit: int = Field(..., ge=1, le=global_settings.max_page_limit)
    results: list
    total: int = Field(..., ge=0)

    class Config:
        orm_mode = True
