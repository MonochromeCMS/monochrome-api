from fastapi import APIRouter, Depends

from ..db import db, models

router = APIRouter(prefix="/autocomplete", tags=["Autocomplete"])


@router.get("/groups", response_model=list[str])
async def get_scan_groups(db_session=Depends(db.db_session)):
    groups = await models.chapter.Chapter.get_groups(db_session)
    if "no group" not in groups:
        groups.append("no group")
    return groups
