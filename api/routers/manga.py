from tempfile import TemporaryFile
from typing import List, Optional
from uuid import UUID

from fastapi import APIRouter, Depends, File, Query, UploadFile, status
from fastapi_permissions import has_permission, permission_exception
from PIL import Image

from ..config import get_settings
from ..db import db, models
from ..exceptions import BadRequestHTTPException, NotFoundHTTPException
from ..media import media
from ..schemas.chapter import ChapterResponse
from ..schemas.manga import MangaResponse, MangaSchema, MangaSearchResponse
from ..utils import logger
from .auth import Permission, get_active_principals, get_connected_user, is_connected
from .responses import manga as responses

global_settings = get_settings()
Chapter = models.chapter.Chapter
Manga = models.manga.Manga
ProgressTracking = models.progress.ProgressTracking
User = models.user.User

router = APIRouter(prefix="/manga", tags=["Manga"])


async def _get_manga(manga_id: UUID, db_session=Depends(db.db_session)):
    return await Manga.find(db_session, manga_id, NotFoundHTTPException("Manga not found"))


@router.post(
    "",
    status_code=status.HTTP_201_CREATED,
    # response_model=MangaResponse, TODO: check why this was disabled
    responses=responses.post_responses,
    dependencies=[Permission("create", Manga.__class_acl__)],
    openapi_extra=responses.needs_auth,
)
async def create_manga(
    payload: MangaSchema,
    user: User = Depends(is_connected),
    db_session=Depends(db.db_session),
):
    manga = Manga(**payload.dict(), owner_id=user.id)
    await manga.save(db_session)
    logger.debug(f"Manga {manga.id} created")
    return manga


@router.get("", response_model=MangaSearchResponse, dependencies=[Permission("view", Manga.__class_acl__)])
async def search_manga(
    title: str = "",
    limit: Optional[int] = Query(10, ge=1, le=global_settings.max_page_limit),
    offset: Optional[int] = Query(0, ge=0),
    db_session=Depends(db.db_session),
):
    count, page = await Manga.search(db_session, title, limit, offset)
    logger.debug(f"Manga page of length {limit} requested with {title} filter, {count} found")

    return {
        "offset": offset,
        "limit": limit,
        "results": page,
        "total": count,
    }


@router.get("/{manga_id}", response_model=MangaResponse, responses=responses.get_responses)
async def get_manga(manga: Manga = Permission("view", _get_manga)):
    logger.debug(f"Manga {manga.id} requested")
    return manga


@router.get(
    "/{manga_id}/chapters",
    response_model=List[ChapterResponse],
    responses=responses.get_chapters_responses,
    openapi_extra=responses.needs_auth,
)
async def get_manga_chapters(
    manga: Manga = Permission("view", _get_manga),
    user_principals=Depends(get_active_principals),
    user: User = Depends(get_connected_user),
    db_session=Depends(db.db_session),
):
    if await has_permission(user_principals, "view", Chapter.__class_acl__()):
        chapters = await Chapter.from_manga(db_session, manga.id)
        if user:
            chapters = [await ProgressTracking.from_chapter(db_session, chapter, user.id) for chapter in chapters]
        return chapters
    else:
        raise permission_exception


@router.delete("/{manga_id}", responses=responses.delete_responses, openapi_extra=responses.needs_auth)
async def delete_manga(manga: Manga = Permission("edit", _get_manga), db_session=Depends(db.db_session)):
    media.media.rmtree(str(manga.id))

    return await manga.delete(db_session)


@router.put(
    "/{manga_id}", response_model=MangaResponse, responses=responses.put_responses, openapi_extra=responses.needs_auth
)
async def update_manga(
    payload: MangaSchema,
    manga: Manga = Permission("edit", _get_manga),
    db_session=Depends(db.db_session),
):
    await manga.update(db_session, **payload.dict())

    return manga


def save_cover(manga_id: UUID, file: File):
    im = Image.open(file)
    with TemporaryFile() as f:
        im.convert("RGB").save(f, "JPEG")
        f.seek(0)
        media.media.put(f"{manga_id}/cover.jpg", f)


@router.put("/{manga_id}/cover", responses=responses.put_cover_responses, openapi_extra=responses.needs_auth)
async def set_manga_cover(
    payload: UploadFile = File(...),
    manga: Manga = Permission("edit", _get_manga),
    db_session=Depends(db.db_session),
):
    if not payload.content_type.startswith("image/"):
        raise BadRequestHTTPException(f"'{payload.filename}' is not an image")

    save_cover(manga.id, payload.file)
    await manga.save(db_session)

    return manga
