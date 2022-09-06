from fastapi import APIRouter, Depends, status

from ..db import db, models
from ..exceptions import NotFoundHTTPException
from ..schemas.progress import ProgressTrackingSchema
from .auth import Permission, is_connected
from .responses import progress as responses

ProgressTracking = models.progress.ProgressTracking
User = models.user.User
Chapter = models.chapter.Chapter

router = APIRouter(prefix="/tracking", tags=["Progress Tracking"])


@router.post(
    "",
    status_code=status.HTTP_201_CREATED,
    response_model=ProgressTrackingSchema,
    responses=responses.post_responses,
    dependencies=[Permission("create", ProgressTracking.__class_acl__)],
    openapi_extra=responses.needs_auth,
)
async def create_tracking(
    payload: ProgressTrackingSchema,
    user: User = Depends(is_connected),
    db_session=Depends(db.db_session),
):
    await Chapter.find(db_session, payload.chapter_id, NotFoundHTTPException("Chapter not found"))

    tracking = await ProgressTracking.get(db_session, payload.chapter_id, user.id)

    if tracking:
        await tracking.update(db_session, **payload.dict())
    else:
        tracking = ProgressTracking(**payload.dict(), author_id=user.id)
        await tracking.save(db_session)

    return tracking
