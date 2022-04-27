from fastapi import APIRouter, Depends

from ..db import db, models
from ..utils import logger

router = APIRouter(prefix="/autocomplete", tags=["Autocomplete"])


@router.get("/groups", response_model=list[str])
async def get_scan_groups(db_session=Depends(db.db_session)):
    logger.debug("Scan groups requested")
    groups = await models.chapter.Chapter.get_groups(db_session)
    if "no group" not in groups:
        logger.debug("Scan groups empty")
        groups.append("no group")
    return groups
