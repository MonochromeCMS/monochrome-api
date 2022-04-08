from typing import Optional
from uuid import UUID

from fastapi import APIRouter, Depends, Query
from fastapi_permissions import has_permission, permission_exception

from ..config import get_settings
from ..db import db, models
from ..exceptions import NotFoundHTTPException
from ..media import media
from ..schemas.chapter import ChapterResponse, ChapterSchema, DetailedChapterResponse, LatestChaptersResponse
from ..schemas.comment import ChapterCommentsResponse
from .auth import Permission, get_active_principals
from .responses import chapter as responses

global_settings = get_settings()
Chapter = models.chapter.Chapter
Comment = models.comment.Comment

router = APIRouter(prefix="/chapter", tags=["Chapter"])


async def _get_chapter(chapter_id: UUID, db_session=Depends(db.db_session)):
    return await Chapter.find(db_session, chapter_id, NotFoundHTTPException("Chapter not found"))


async def _get_detailed_chapter(chapter_id: UUID, db_session=Depends(db.db_session)):
    return await Chapter.find_detailed(db_session, chapter_id, NotFoundHTTPException("Chapter not found"))


@router.get("", response_model=LatestChaptersResponse, dependencies=[Permission("view", Chapter.__class_acl__)])
async def get_latest_chapters(
    limit: Optional[int] = Query(10, ge=1, le=global_settings.max_page_limit),
    offset: Optional[int] = Query(0, ge=0),
    db_session=Depends(db.db_session),
):
    count, page = await Chapter.latest(db_session, limit, offset)

    return {
        "offset": offset,
        "limit": limit,
        "results": page,
        "total": count,
    }


@router.get("/{chapter_id}", response_model=DetailedChapterResponse, responses=responses.get_responses)
async def get_chapter(chapter: Chapter = Permission("view", _get_detailed_chapter)):
    return chapter


@router.delete("/{chapter_id}", responses=responses.delete_responses)
async def delete_chapter(chapter: Chapter = Permission("edit", _get_chapter), db_session=Depends(db.db_session)):
    media.media.rmtree(f"{chapter.manga_id}/{chapter.id}")

    return await chapter.delete(db_session)


@router.put("/{chapter_id}", response_model=ChapterResponse, responses=responses.put_responses)
async def update_chapter(
    payload: ChapterSchema,
    chapter: Chapter = Permission("edit", _get_chapter),
    db_session=Depends(db.db_session),
):
    await chapter.update(db_session, **payload.dict())
    return chapter


@router.get(
    "/{chapter_id}/comments", response_model=ChapterCommentsResponse, responses=responses.get_comments_responses
)
async def get_chapter_comments(
    limit: Optional[int] = Query(10, ge=1, le=global_settings.max_page_limit),
    offset: Optional[int] = Query(0, ge=0),
    chapter: Chapter = Permission("view", _get_chapter),
    user_principals=Depends(get_active_principals),
    db_session=Depends(db.db_session),
):
    if await has_permission(user_principals, "view", Comment.__class_acl__()):
        count, page = await Comment.from_chapter(db_session, chapter.id, limit, offset)
        return {
            "offset": offset,
            "limit": limit,
            "results": page,
            "total": count,
        }
    else:
        raise permission_exception
