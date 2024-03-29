from fastapi import APIRouter, Depends

from ..db import db, models
from ..schemas.settings import SettingsSchema
from ..utils import logger
from .auth import Permission
from .responses import settings as responses

Settings = models.settings.Settings

router = APIRouter(prefix="/settings", tags=["Settings"])


async def _get_settings(db_session=Depends(db.db_session)):
    return await Settings.get(db_session)


@router.get("", response_model=SettingsSchema)
async def get_site_settings(settings: Settings = Permission("view", _get_settings)):
    return SettingsSchema.from_orm(settings)


@router.put("", responses=responses.put_responses, openapi_extra=responses.needs_auth)
async def edit_site_settings(
    new_settings: SettingsSchema,
    settings: Settings = Permission("edit", _get_settings),
    db_session=Depends(db.db_session),
):
    logger.debug("Settings updated")
    logger.debug(f"Old settings: {settings}")
    logger.debug(f"New settings: {new_settings}")
    await settings.set(db_session, **new_settings.dict())
    return settings
