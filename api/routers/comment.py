from uuid import UUID

from fastapi import APIRouter, Depends, status

from ..db import db, models
from ..exceptions import BadRequestHTTPException, NotFoundHTTPException
from ..schemas.comment import CommentEditSchema, CommentResponse, CommentSchema
from ..utils import logger
from .auth import Permission, get_connected_user
from .responses import comment as responses

Comment = models.comment.Comment
User = models.user.User

router = APIRouter(prefix="/comment", tags=["Comment"])


async def _get_comment(comment_id: UUID, db_session=Depends(db.db_session)):
    return await Comment.find(db_session, comment_id, NotFoundHTTPException("Comment not found"))


@router.post(
    "",
    status_code=status.HTTP_201_CREATED,
    response_model=CommentResponse,
    responses=responses.post_responses,
    dependencies=[Permission("create", Comment.__class_acl__)],
)
async def create_comment(
    payload: CommentSchema,
    user: User = Depends(get_connected_user),
    db_session=Depends(db.db_session),
):
    if payload.reply_to:
        reply_comment: Comment = await Comment.find(db_session, payload.reply_to, None)
        if not reply_comment or reply_comment.chapter_id != payload.chapter_id:
            raise BadRequestHTTPException("Comment to reply to not valid")

    comment = Comment(**payload.dict(), author_id=user.id)
    await comment.save(db_session)
    logger.debug(f"Comment created on {payload.chapter_id}")

    return comment


@router.get("/{comment_id}", response_model=CommentResponse, responses=responses.get_responses)
async def get_comment(comment: Comment = Permission("view", _get_comment)):
    logger.debug(f"Comment {comment.id} requested")
    return comment


@router.delete("/{comment_id}", responses=responses.delete_responses)
async def delete_comment(comment: Comment = Permission("edit", _get_comment), db_session=Depends(db.db_session)):
    logger.debug(f"Comment {comment.id} deleted")
    return await comment.delete(db_session)


@router.put("/{comment_id}", response_model=CommentResponse, responses=responses.put_responses)
async def update_comment(
    payload: CommentEditSchema,
    comment: Comment = Permission("edit", _get_comment),
    db_session=Depends(db.db_session),
):
    logger.debug(f"Comment {comment.id} updated")
    logger.debug(f"Old comment: {comment}")
    logger.debug(f"New comment: {payload}")
    await comment.update(db_session, **payload.dict())
    return comment
