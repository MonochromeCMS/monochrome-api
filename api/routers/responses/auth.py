from ...exceptions import AuthFailedHTTPException, PermissionsHTTPException
from ...schemas.user import TokenResponse

auth_responses = {
    401: {
        "description": "User isn't authenticated",
        **AuthFailedHTTPException.open_api(),
    },
    403: {
        "description": "User doesn't have the permission to perform this action",
        **PermissionsHTTPException.open_api(),
    },
}

token_responses = {
    200: {"description": "A token for the logged in user", "model": TokenResponse},
    401: {
        "description": "Credentials don't match",
        **AuthFailedHTTPException.open_api("Wrong username/password"),
    },
}

logout_everywhere_responses = {
    **auth_responses,
    200: {
        "description": "User was logged out from every device",
        "content": {
            "application/json": {
                "example": "OK",
            },
        },
    },
}
