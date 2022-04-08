from typing import Dict, Optional

from fastapi import HTTPException, status

from .utils import slugify


class BaseHTTPException(HTTPException):
    default: str = "Error"
    code: int = 500

    def __init__(self, msg: Optional[str] = None, **kwargs):
        super().__init__(status_code=self.code, detail=msg or self.default, **kwargs)

    @classmethod
    def open_api(cls, msg: Optional[str] = None):
        """The OpenAPI spec for this exception."""
        return {
            "content": {
                "application/json": {
                    "example": {
                        "detail": msg if msg else cls.default,
                    },
                },
            },
        }

    @classmethod
    def open_api_list(cls, msgs: Dict[str, str]):
        """The OpenAPI spec for this exception, but with different examples."""
        return {
            "content": {
                "application/json": {
                    "examples": {
                        slugify(k): {
                            "summary": k,
                            "value": {
                                "detail": v,
                            },
                        }
                        for (k, v) in msgs.items()
                    },
                },
            },
        }


class BadRequestHTTPException(BaseHTTPException):
    code = status.HTTP_400_BAD_REQUEST
    default = "Bad request"


class ForbiddenHTTPException(BaseHTTPException):
    code = status.HTTP_403_FORBIDDEN
    default = "Forbidden access to resource"


class NotFoundHTTPException(BaseHTTPException):
    code = status.HTTP_404_NOT_FOUND
    default = "Resource not found"


class ConflictHTTPException(BaseHTTPException):
    code = status.HTTP_409_CONFLICT
    default = "Conflicting resource request"


class ServiceNotAvailableHTTPException(BaseHTTPException):
    code = status.HTTP_503_SERVICE_UNAVAILABLE
    default = "Service not available"


class UnprocessableEntityHTTPException(BaseHTTPException):
    code = status.HTTP_422_UNPROCESSABLE_ENTITY
    default = "The entity couldn't be processed"


class AuthFailedHTTPException(BaseHTTPException):
    code = status.HTTP_401_UNAUTHORIZED
    default = "Could not validate credentials"

    def __init__(self, msg: Optional[str] = None):
        # OAuth spec requires this header in errors
        super().__init__(
            msg,
            headers={"WWW-Authenticate": "Bearer"},
        )


class PermissionsHTTPException(AuthFailedHTTPException):
    code = status.HTTP_403_FORBIDDEN
    default = "Not enough permissions to access resource"
