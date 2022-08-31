from fastapi import FastAPI
from fastapi.openapi.utils import get_openapi


def custom_openapi(app: FastAPI):
    def wrapper():
        if app.openapi_schema:
            return app.openapi_schema

        openapi_schema = get_openapi(
            title="Monochrome API",
            version="2.1.0",
            description="Monochrome is an open source manga CMS",
            routes=app.routes,
        )

        # Custom documentation fastapi-jwt-auth
        security_schemes = {
            "OAuth2PasswordBearer": {
                "type": "oauth2",
                "flows": {"password": {"scopes": {}, "tokenUrl": "auth/token", "refreshUrl": "auth/refresh"}},
            },
        }

        openapi_schema["components"]["securitySchemes"] = security_schemes
        
        for name, value in openapi_schema["components"]["schemas"].items():
            if "_" in name:
                value["title"] = value["title"].replace("_", " ")

        app.openapi_schema = openapi_schema

        return app.openapi_schema

    return wrapper
