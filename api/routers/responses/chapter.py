from ...exceptions import NotFoundHTTPException
from ...schemas.chapter import ChapterResponse, DetailedChapterResponse
from ...schemas.comment import ChapterCommentsResponse
from .auth import auth_responses

get_responses = {
    200: {
        "description": "The requested chapter",
        "model": DetailedChapterResponse,
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
        "description": "The chapter was deleted",
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
        "description": "The edited chapter",
        "model": ChapterResponse,
    },
}

get_comments_responses = {
    **get_responses,
    200: {
        "description": "The chapter's comments",
        "model": ChapterCommentsResponse,
    },
}
