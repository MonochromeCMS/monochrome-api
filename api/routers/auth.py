from typing import Optional
from uuid import UUID

from fastapi import APIRouter, Depends, Request
from fastapi.security import OAuth2PasswordRequestForm
from fastapi_jwt_auth import AuthJWT
from fastapi_permissions import Authenticated, Everyone, configure_permissions
from passlib.context import CryptContext

from ..config import get_settings
from ..db import db, models
from ..exceptions import AuthFailedHTTPException
from ..limiter import limiter
from ..schemas.user import TokenResponse
from ..utils import logger
from .responses import auth as responses

global_settings = get_settings()
User = models.user.User


@AuthJWT.load_config
def get_jwt_config():
    return global_settings.authjwt


router = APIRouter(tags=["Auth"], prefix="/auth")

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")


# UTILS


def password_hash(password: str):
    return pwd_context.hash(password)


async def authenticate_user(db_session, username: str, password: str):
    """
    Returns a User if the credentials match.
    """
    user: User = await User.from_username_email(db_session, username)
    if user and pwd_context.verify(password, user.hashed_password):
        return user
    else:
        return None


def token_response(user_id: UUID, Authorize: AuthJWT, refresh=True):
    access_token = Authorize.create_access_token(subject=str(user_id), fresh=refresh)
    refresh_token = Authorize.create_refresh_token(subject=str(user_id)) if refresh else None

    Authorize.set_access_cookies(access_token)
    if refresh:
        Authorize.set_refresh_cookies(refresh_token)

    return {
        "token_type": "bearer",
        "access_token": access_token,
        "refresh_token": refresh_token,
    }


# DEPENDENCIES


async def get_connected_user(db_session=Depends(db.db_session), Authorize: AuthJWT = Depends()):
    Authorize.jwt_optional()
    subject = Authorize.get_jwt_subject()
    jwt = Authorize.get_raw_jwt()

    if subject:
        user: Optional[User] = await User.find(db_session, UUID(subject), exception=None)
    else:
        user = None

    if user:
        iat = jwt.get("iat")

        if iat < user.update_time.timestamp():
            return None

    return user


async def is_connected(user: User = Depends(get_connected_user), Authorize: AuthJWT = Depends()):
    Authorize.jwt_required()

    return user


async def get_active_principals(user: User = Depends(get_connected_user)):
    if user:
        principals = [Everyone, Authenticated]
        principals.extend(getattr(user, "principals", []))
    else:
        principals = [Everyone]
    return principals


# ROUTING


Permission = configure_permissions(get_active_principals)


@router.post("/token", response_model=TokenResponse, responses=responses.token_responses)
@limiter.limit("10/minute")
async def login(
    request: Request,
    Authorize: AuthJWT = Depends(),
    form_data: OAuth2PasswordRequestForm = Depends(),
    db_session=Depends(db.db_session),
):
    """Provides an OAuth2 token if the credentials are right."""
    user = await authenticate_user(db_session, form_data.username, form_data.password)
    if not user:
        logger.debug("Failed login")
        raise AuthFailedHTTPException("Wrong username/password")
    logger.debug(f"{user.username} logged in")
    return token_response(user.id, Authorize)


@router.post("/refresh", response_model=TokenResponse, responses=responses.token_responses)
@limiter.limit("1/minute")
async def refresh_access_token(request: Request, Authorize: AuthJWT = Depends(), db_session=Depends(db.db_session)):
    # TODO: Frontend send refresh via headers, only get access token back
    Authorize.jwt_refresh_token_required()

    subject = Authorize.get_jwt_subject()
    user: Optional[User] = await User.find(db_session, UUID(subject), exception=None)
    if not user:
        raise AuthFailedHTTPException("User not found")

    logger.debug(f"{user.username} refreshed its tokens")
    return token_response(user.id, Authorize, refresh=False)


@router.delete("/logout")
def logout(Authorize: AuthJWT = Depends()):
    Authorize.jwt_required()

    Authorize.unset_jwt_cookies()
    return {"msg": "Successful logout"}


@router.delete("/logout_everywhere", responses=responses.logout_everywhere_responses)
async def logout_everywhere(
    user: User = Depends(is_connected), db_session=Depends(db.db_session), Authorize: AuthJWT = Depends()
):
    await user.save(db_session)
    Authorize.unset_jwt_cookies()
    logger.debug(f"{user.username} logged out everywhere")
    return {"msg": "Successful logout everywhere"}
