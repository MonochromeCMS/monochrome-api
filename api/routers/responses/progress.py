from ...exceptions import NotFoundHTTPException
from ...schemas.progress import ProgressTrackingSchema
from .auth import auth_responses, needs_auth

needs_auth = needs_auth

post_responses = {
    **auth_responses,
    404: {
        "description": "The chapter couldn't be found",
        **NotFoundHTTPException.open_api("Chapter not found"),
    },
    201: {
        "description": "The created tracking",
        "model": ProgressTrackingSchema,
    },
}
