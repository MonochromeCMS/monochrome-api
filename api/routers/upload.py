from tempfile import TemporaryFile
from typing import List
from uuid import UUID

from fastapi import APIRouter, BackgroundTasks, Depends, File, UploadFile, status
from fastapi.encoders import jsonable_encoder
from fastapi.responses import ORJSONResponse
from fastapi_permissions import has_permission, permission_exception

from ..config import get_settings
from ..db import db, models
from ..exceptions import BadRequestHTTPException, NotFoundHTTPException
from ..media import media
from ..schemas.chapter import ChapterResponse
from ..schemas.upload import CommitUploadSession, UploadedBlobResponse, UploadSessionResponse, UploadSessionSchema
from ..utils import logger
from .auth import Permission, get_active_principals, is_connected
from .responses import upload as responses
from .utils import upload as utils

global_settings = get_settings()
UploadSession = models.upload.UploadSession
UploadedBlob = models.upload.UploadedBlob
User = models.user.User
Manga = models.manga.Manga
Chapter = models.chapter.Chapter

router = APIRouter(prefix="/upload", tags=["Upload"])


async def _get_upload_session(session_id: UUID, db_session=Depends(db.db_session)):
    return await UploadSession.find(db_session, session_id, NotFoundHTTPException("Session not found"))


async def _get_upload_session_blobs(session_id: UUID, db_session=Depends(db.db_session)):
    return await UploadSession.find_detailed(db_session, session_id, NotFoundHTTPException("Session not found"))


@router.post(
    "/begin",
    status_code=status.HTTP_201_CREATED,
    response_model=UploadSessionResponse,
    responses=responses.post_responses,
    openapi_extra=responses.needs_auth,
)
async def begin_upload_session(
    payload: UploadSessionSchema,
    user: User = Depends(is_connected),
    user_principals=Depends(get_active_principals),
    _: UploadSession = Permission("create", UploadSession.__class_acl__),
    db_session=Depends(db.db_session),
):
    await Manga.find(db_session, payload.manga_id, NotFoundHTTPException("Manga not found"))
    # `chapter_id` enables edit mode, only allow those with edit permissions
    if payload.chapter_id:
        chapter: Chapter = await Chapter.find(
            db_session, payload.chapter_id, NotFoundHTTPException("Chapter not found")
        )
        if chapter.manga_id != payload.manga_id:
            raise BadRequestHTTPException("The provided chapter doesn't belong to this manga")
        elif not await has_permission(user_principals, "edit", chapter):
            raise permission_exception
    else:
        chapter = None

    session = UploadSession(**payload.dict(), owner_id=user.id)
    await session.save(db_session)

    logger.debug(f"Upload session {session.id} created")

    utils.TempDir(str(session.id)).setup()

    if chapter:
        logger.debug(f"Upload session {session.id}: Edit mode")
        blobs = await utils.uploaded_blob_list(db_session, session.id, chapter.length)
        logger.debug(f"Upload session {session.id}: blobs = {blobs}")
        utils.copy_chapter_to_session(chapter, blobs)

    return await UploadSession.find_detailed(db_session, session.id)


@router.get(
    "/{session_id}",
    response_model=UploadSessionResponse,
    responses=responses.get_responses,
    openapi_extra=responses.needs_auth,
)
async def get_upload_session(upload_session=Permission("view", _get_upload_session_blobs)):
    logger.debug(f"Upload session {upload_session.id} requested")
    return upload_session


@router.post(
    "/{session_id}",
    status_code=status.HTTP_201_CREATED,
    response_model=list[UploadedBlobResponse],
    responses=responses.post_blobs_responses,
    openapi_extra=responses.needs_auth,
)
async def upload_pages_to_upload_session(
    payload: list[UploadFile] = File(...),
    session=Permission("edit", _get_upload_session),
    db_session=Depends(db.db_session),
):
    for file in payload:
        if not utils.valid_mime(file.content_type):
            raise BadRequestHTTPException(f"'{file.filename}'s format is not supported")

    tmp = utils.TempDir(session.id)

    blobs = []
    for file in payload:
        if file.content_type in utils.compressed_formats:
            files = await utils.decompress_file(file, tmp.zip, tmp.files)
        else:
            files = await utils.save_single_file(file, tmp.files)

        file_blobs: List[UUID] = []
        for f in files:
            file_blob = UploadedBlob(session_id=session.id, name=f)
            await file_blob.save(db_session)

            blobs.append(file_blob)
            file_blobs.append(file_blob.id)

        utils.save_session_image(zip(file_blobs, (tmp.files_join(f) for f in files)))

    return blobs


@router.delete("/{session_id}", responses=responses.delete_responses, openapi_extra=responses.needs_auth)
async def delete_upload_session(
    tasks: BackgroundTasks, session=Permission("edit", _get_upload_session_blobs), db_session=Depends(db.db_session)
):
    session_images = (b.id for b in session.blobs)
    await session.delete()

    utils.TempDir(session.id).rm()
    tasks.add_task(utils.delete_blobs, session_images)
    return "OK"


@router.post(
    "/{session_id}/commit",
    response_model=ChapterResponse,
    responses=responses.post_commit_responses,
    openapi_extra=responses.needs_auth,
)
async def commit_upload_session(
    payload: CommitUploadSession,
    tasks: BackgroundTasks,
    session: UploadSession = Permission("edit", _get_upload_session_blobs),
    db_session=Depends(db.db_session),
):
    blobs = set(b.id for b in session.blobs)
    edit = session.chapter_id is not None

    if not len(payload.page_order) > 0:
        raise BadRequestHTTPException("At least one page needs to be provided")
    if len(payload.page_order) != len(set(payload.page_order)):
        raise BadRequestHTTPException("Some pages are identical")
    if len(set(payload.page_order).difference(blobs)) > 0:
        raise BadRequestHTTPException("Some pages don't belong to this session")

    if edit:
        chapter = await Chapter.find(db_session, session.chapter_id, NotFoundHTTPException("Chapter not found"))
        await chapter.update(db_session, length=len(payload.page_order), **payload.chapter_draft.dict())
    else:
        chapter = Chapter(
            manga_id=session.manga_id,
            length=len(payload.page_order),
            owner_id=session.owner_id,
            **payload.chapter_draft.dict(),
        )
        await chapter.save(db_session)

    utils.TempDir(session.id).rm()
    await session.delete(db_session)

    tasks.add_task(utils.commit_blobs, chapter, payload.page_order, edit)
    tasks.add_task(utils.delete_blobs, blobs.difference(payload.page_order))

    content = jsonable_encoder(ChapterResponse.from_orm(chapter))
    return ORJSONResponse(status_code=(200 if edit else 201), content=content)


@router.delete(
    "/{session_id}/files", responses=responses.delete_all_blobs_responses, openapi_extra=responses.needs_auth
)
async def delete_all_pages_from_upload_session(
    tasks: BackgroundTasks,
    session=Permission("edit", _get_upload_session_blobs),
    db_session=Depends(db.db_session),
):
    session_images = set(b.id for b in session.blobs)
    tasks.add_task(utils.delete_blobs, session_images)

    for blob in session.blobs:
        await blob.delete(db_session)

    return "OK"


@router.delete("/{session_id}/{file_id}", responses=responses.delete_blob_responses, openapi_extra=responses.needs_auth)
async def delete_page_from_upload_session(
    file_id: UUID,
    tasks: BackgroundTasks,
    session: UploadSession = Permission("edit", _get_upload_session_blobs),
    db_session=Depends(db.db_session),
):
    if file_id not in (b.id for b in session.blobs):
        raise BadRequestHTTPException("The blob doesn't exist in the session")

    blob = await UploadedBlob.find(db_session, file_id, NotFoundHTTPException("Blob not found"))
    await blob.delete(db_session)

    tasks.add_task(utils.delete_blobs, (file_id,))
    return "OK"


@router.post(
    "/{session_id}/slice",
    status_code=status.HTTP_201_CREATED,
    response_model=List[UploadedBlobResponse],
    responses=responses.slice_blobs_responses,
    openapi_extra=responses.needs_auth,
)
async def slice_pages_in_upload_session(
    payload: list[UUID],
    tasks: BackgroundTasks,
    session: UploadSession = Permission("edit", _get_upload_session_blobs),
    db_session=Depends(db.db_session),
):
    blobs = set(b.id for b in session.blobs)

    if not len(payload) > 0:
        raise BadRequestHTTPException("At least one page needs to be provided")
    if len(set(payload).difference(blobs)) > 0:
        raise BadRequestHTTPException("Some pages don't belong to this session")

    parts = utils.concat_and_cut_images(payload)

    for i, part in enumerate(parts):
        file_blob = UploadedBlob(session_id=session.id, name=f"slice_{i+1}.jpg")
        await file_blob.save(db_session)

        with TemporaryFile() as f:
            part.save(f, "JPEG")
            f.seek(0)
            media.media.put(f"blobs/{file_blob.id}.jpg", f)

        part.close()

    for blob_id in payload:
        blob: UploadedBlob = await UploadedBlob.find(db_session, blob_id)
        await blob.delete(db_session)

    tasks.add_task(utils.delete_blobs, payload)

    return await UploadedBlob.from_session(db_session, session.id)
