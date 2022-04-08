from ...exceptions import BadRequestHTTPException, NotFoundHTTPException
from ...schemas.chapter import ChapterResponse
from ...schemas.manga import MangaResponse
from .auth import auth_responses

post_responses = {
    **auth_responses,
    201: {
        "description": "The created manga",
        "model": MangaResponse,
    },
}

get_responses = {
    404: {
        "description": "The manga couldn't be found",
        **NotFoundHTTPException.open_api("Manga not found"),
    },
    200: {
        "description": "The requested manga",
        "model": MangaResponse,
    },
}

get_chapters_responses = {
    **get_responses,
    200: {
        "description": "The requested chapters",
        "model": list[ChapterResponse],
    },
}

delete_responses = {
    **auth_responses,
    **get_responses,
    200: {
        "description": "The manga was deleted",
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
        "description": "The edited manga",
        "model": MangaResponse,
    },
}

put_cover_responses = {
    **auth_responses,
    **get_responses,
    400: {
        "description": "The cover isn't a valid image",
        **BadRequestHTTPException.open_api("<image_name> is not an image"),
    },
    200: {
        "description": "The edited manga",
        "model": MangaResponse,
    },
}
