from ...exceptions import BadRequestHTTPException, NotFoundHTTPException
from ...schemas.comment import CommentResponse
from .auth import auth_responses

post_responses = {
    **auth_responses,
    400: {
        "description": "The replied comment is not valid",
        **BadRequestHTTPException.open_api("Comment to reply to not valid"),
    },
    201: {
        "description": "The created comment",
        "model": CommentResponse,
    },
}

get_responses = {
    200: {
        "description": "The requested comment",
        "model": CommentResponse,
    },
    404: {
        "description": "The chapter couldn't be found",
        **NotFoundHTTPException.open_api("Chapter not found"),
    },
}

delete_responses = {
    **auth_responses,
    **get_responses,
    200: {
        "description": "The comment was deleted",
        "content": {
            "application/json": {
                "example": "OK",
            },
        },
    },
}

put_responses = {
    **auth_responses,
    **get_responses,
    200: {
        "description": "The edited comment",
        "model": CommentResponse,
    },
}
