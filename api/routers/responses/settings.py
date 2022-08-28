from ...schemas.settings import SettingsSchema
from .auth import auth_responses, needs_auth

needs_auth = needs_auth

put_responses = {
    **auth_responses,
    200: {
        "description": "The website settings",
        "model": SettingsSchema,
    },
}
