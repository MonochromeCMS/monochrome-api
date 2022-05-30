from datetime import datetime, timedelta
from typing import Optional
from uuid import UUID

from fastapi import APIRouter, Depends, Request
from fastapi.security import OAuth2PasswordBearer, OAuth2PasswordRequestForm
from fastapi_permissions import Authenticated, Everyone, configure_permissions
from jose import JWTError, jwt
from passlib.context import CryptContext

from ..config import get_settings
from ..db import db, models
from ..exceptions import AuthFailedHTTPException
from ..limiter import limiter
from ..schemas.user import RefreshToken, TokenContent, TokenResponse
from ..utils import logger
from .responses import auth as responses

global_settings = get_settings()
User = models.user.User

router = APIRouter(tags=["Auth"], prefix="/auth")

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="auth/token", auto_error=False)

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


def create_token(sub: UUID, typ: str, expires_delta: Optional[timedelta] = None):
    if expires_delta:
        expire = datetime.utcnow() + expires_delta
    else:
        expire = datetime.utcnow() + timedelta(minutes=15)
    to_encode = TokenContent(sub=str(sub), exp=expire, iat=datetime.utcnow(), typ=typ).dict()
    encoded_jwt = jwt.encode(to_encode, global_settings.jwt_secret_key, algorithm=global_settings.jwt_algorithm)
    return encoded_jwt


def decode_token(token: str):
    try:
        payload = jwt.decode(token, global_settings.jwt_secret_key, algorithms=[global_settings.jwt_algorithm])
        id: str = payload.get("sub")
        if id is not None:
            return payload
        else:
            return None
    except JWTError:
        return None


async def validate_refresh_token(token: str, db_session):
    decoded_token = decode_token(token)

    if not decoded_token or decoded_token.get("typ") != "refresh":
        raise AuthFailedHTTPException("Invalid token")

    id = decoded_token.get("sub")
    user: Optional[User] = await User.find(db_session, UUID(id), exception=None)
    iat = decoded_token.get("iat")

    if iat < user.update_time.timestamp():
        return None

    return user


def token_response(user: User):
    access_token_expires = timedelta(minutes=global_settings.jwt_access_token_expire_minutes)
    refresh_token_expires = timedelta(days=15)

    access_token = create_token(sub=user.id, typ="session", expires_delta=access_token_expires)
    refresh_token = create_token(sub=user.id, typ="refresh", expires_delta=refresh_token_expires)
    return {
        "token_type": "bearer",
        "access_token": access_token,
        "refresh_token": refresh_token,
    }


# DEPENDENCIES


async def get_connected_user(db_session=Depends(db.db_session), token: str = Depends(oauth2_scheme)):
    if not token:
        return None
    decoded_token = decode_token(token)

    if not decoded_token or decoded_token.get("typ") != "session":
        return None

    id = decoded_token.get("sub")
    user: Optional[User] = await User.find(db_session, UUID(id), exception=None)
    iat = decoded_token.get("iat")

    if iat < user.update_time.timestamp():
        return None

    return user


async def is_connected(user: User = Depends(get_connected_user)):
    if user:
        return user
    else:
        raise AuthFailedHTTPException()


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
async def login_for_access_token(
    request: Request,
    form_data: OAuth2PasswordRequestForm = Depends(),
    db_session=Depends(db.db_session),
):
    """Provides an OAuth2 token if the credentials are right."""
    user = await authenticate_user(db_session, form_data.username, form_data.password)
    if not user:
        logger.debug("Failed login")
        raise AuthFailedHTTPException("Wrong username/password")
    logger.debug(f"{user.username} logged in")
    return token_response(user)


@router.post("/refresh", response_model=TokenResponse, responses=responses.token_responses)
@limiter.limit("1/minute")
async def refresh_access_token(request: Request, body: RefreshToken, db_session=Depends(db.db_session)):
    user = await validate_refresh_token(body.token, db_session)
    logger.debug(f"{user.username} refreshed its tokens")
    return token_response(user)


@router.post("/logout_everywhere", responses=responses.logout_everywhere_responses)
async def logout_everywhere(user: User = Depends(is_connected), db_session=Depends(db.db_session)):
    await user.save(db_session)
    logger.debug(f"{user.username} logged out everywhere")
    return "OK"
