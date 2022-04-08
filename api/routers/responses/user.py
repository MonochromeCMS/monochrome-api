from ...exceptions import BadRequestHTTPException, NotFoundHTTPException
from ...schemas.user import UserResponse, UsersResponse
from .auth import auth_responses

get_me_responses = {
    **auth_responses,
    200: {
        "description": "The current user",
        "model": UserResponse,
    },
}


get_responses = {
    **auth_responses,
    404: {
        "description": "The user couldn't be found",
        **NotFoundHTTPException.open_api("User not found"),
    },
    200: {
        "description": "The requested user",
        "model": UserResponse,
    },
}

put_responses = {
    **get_responses,
    400: {
        "description": "Existing user",
        **BadRequestHTTPException.open_api("That username or email is already in use"),
    },
    200: {
        "description": "The edited user",
        "model": UserResponse,
    },
}

delete_responses = {
    **get_responses,
    400: {
        "description": "Own user",
        **BadRequestHTTPException.open_api("You can't delete your own user"),
    },
    200: {
        "description": "The user was deleted",
        "content": {
            "application/json": {
                "example": "OK",
            },
        },
    },
}

post_responses = {
    **auth_responses,
    400: {
        "description": "Existing user",
        **BadRequestHTTPException.open_api("That username or email is already in use"),
    },
    201: {
        "description": "The created user",
        "model": UserResponse,
    },
}

register_responses = {
    400: {
        "description": "Existing user",
        **BadRequestHTTPException.open_api("That username or email is already in use"),
    },
    201: {
        "description": "The created user",
        "model": UserResponse,
    },
}

get_all_responses = {
    **auth_responses,
    200: {
        "description": "The created user",
        "model": UsersResponse,
    },
}

put_avatar_responses = {
    **get_responses,
    400: {
        "description": "The avatar isn't a valid image",
        **BadRequestHTTPException.open_api("<image_name> is not an image"),
    },
    200: {
        "description": "The edited user",
        "model": UserResponse,
    },
}
