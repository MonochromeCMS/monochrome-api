from tempfile import TemporaryFile
from typing import Optional
from uuid import UUID

from fastapi import APIRouter, Depends, File, Query, Request, UploadFile, status
from fastapi_permissions import has_permission
from PIL import Image

from ..config import get_settings
from ..db import db, models
from ..exceptions import BadRequestHTTPException, NotFoundHTTPException
from ..limiter import limiter
from ..media import media
from ..schemas.user import UserEditSchema, UserFilters, UserRegisterSchema, UserResponse, UserSchema, UsersResponse
from .auth import Permission, get_active_principals, is_connected, password_hash
from .responses import user as responses

global_settings = get_settings()
User = models.user.User
Role = models.user.Role

router = APIRouter(
    prefix="/user",
    tags=["User"],
)


async def _get_user(user_id: UUID, db_session=Depends(db.db_session)):
    return await User.find(db_session, user_id, NotFoundHTTPException("User not found"))


@router.get(
    "/me", response_model=UserResponse, responses=responses.get_me_responses, openapi_extra=responses.needs_auth
)
async def get_current_user(user: User = Depends(is_connected)):
    """Provides information about the user logged in."""
    return user


@router.get(
    "/{user_id}", response_model=UserResponse, responses=responses.get_responses, openapi_extra=responses.needs_auth
)
async def get_user(user: User = Permission("view", _get_user)):
    """Provides information about a user."""
    return user


@router.put(
    "/{user_id}", response_model=UserResponse, responses=responses.put_responses, openapi_extra=responses.needs_auth
)
async def update_user(
    payload: UserEditSchema,
    user: User = Permission("edit", _get_user),
    user_principals=Depends(get_active_principals),
    db_session=Depends(db.db_session),
):
    """
    Update an user details, only allowed if you are that user, or if you are an Admin
    Only an Admin can change a user's role.
    """

    if await User.from_username(db_session, payload.username, user.id):
        raise BadRequestHTTPException("That username is already in use")

    if await User.from_email(db_session, payload.email, user.id):
        raise BadRequestHTTPException("That email is already in use")

    data = payload.dict(exclude={"password"})

    if not await has_permission(user_principals, "edit", User.__class_acl__()):
        # Only someone that can edit all users can edit their roles
        data.pop("role")

    if payload.password:
        data["hashed_password"] = password_hash(payload.password)
    await user.update(db_session, **data)

    return user


@router.delete("/{user_id}", responses=responses.delete_responses, openapi_extra=responses.needs_auth)
async def delete_user(user: User = Permission("edit", _get_user), db_session=Depends(db.db_session)):
    """Delete an user, only allowed if you are that user, or if you are an Admin"""
    return await user.delete(db_session)


@router.post(
    "",
    status_code=status.HTTP_201_CREATED,
    response_model=UserResponse,
    responses=responses.post_responses,
    dependencies=[Permission("create", User.__class_acl__)],
    openapi_extra=responses.needs_auth,
)
async def create_user(payload: UserSchema, db_session=Depends(db.db_session)):
    """Create an user, only allowed for Admins"""
    if await User.from_username(db_session, payload.username):
        raise BadRequestHTTPException("That username is already in use")
    if await User.from_email(db_session, payload.email):
        raise BadRequestHTTPException("That email is already in use")

    data = payload.dict(exclude={"password"})
    hashed_pwd = password_hash(payload.password)
    user = User(**data, hashed_password=hashed_pwd)

    await user.save(db_session)
    return user


if global_settings.allow_registration:

    @router.post(
        "/register",
        response_model=UserResponse,
        status_code=status.HTTP_201_CREATED,
        responses=responses.register_responses,
        dependencies=[Permission("register", User.__class_acl__)],
    )
    @limiter.limit("5/minute")
    async def register_user(request: Request, payload: UserRegisterSchema, db_session=Depends(db.db_session)):
        """Register a new user, they will be given the User role."""
        hashed_pwd = password_hash(payload.password)

        if await User.from_username_email(db_session, payload.username, payload.email):
            raise BadRequestHTTPException("That username or email is already in use")

        data = payload.dict(exclude={"password"})
        user = User(**data, role=Role.user, hashed_password=hashed_pwd)
        await user.save(db_session)

        return user


@router.get("", response_model=UsersResponse, responses=responses.get_all_responses, openapi_extra=responses.needs_auth)
async def search_users(
    limit: Optional[int] = Query(10, ge=1, le=global_settings.max_page_limit),
    offset: Optional[int] = Query(0, ge=0),
    username: str = "",
    role: Optional[Role] = None,
    email: Optional[str] = None,
    user_id: Optional[UUID] = None,
    _: User = Permission("view", User.__class_acl__),
    db_session=Depends(db.db_session),
):
    count, page = await User.search(
        db_session, username, UserFilters(role=role, email=email, id=user_id), limit, offset
    )

    return {
        "offset": offset,
        "limit": limit,
        "results": page,
        "total": count,
    }


def save_avatar(user_id: UUID, file: File):
    im = Image.open(file)
    with TemporaryFile() as f:
        im.convert("RGB").save(f, "JPEG")
        f.seek(0)
        media.media.put(f"users/{user_id}.jpg", f)


@router.put("/{user_id}/avatar", responses=responses.put_avatar_responses, openapi_extra=responses.needs_auth)
async def set_avatar(
    payload: UploadFile = File(...),
    user: User = Permission("edit", _get_user),
    db_session=Depends(db.db_session),
):
    if not payload.content_type.startswith("image/"):
        raise BadRequestHTTPException(f"'{payload.filename}' is not an image")

    save_avatar(user.id, payload.file)
    await user.save(db_session)

    return user
