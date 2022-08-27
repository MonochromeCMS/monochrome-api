from datetime import timedelta
from enum import Enum
from functools import lru_cache

from pydantic import BaseSettings, Field

from .utils import logger


class MediaBackends(str, Enum):
    deta = "DETA"
    filesystem = "FS"


class DatabaseBackends(str, Enum):
    deta = "DETA"
    postgres = "POSTGRES"


class Settings(BaseSettings):
    media_backend: MediaBackends
    db_backend: DatabaseBackends
    # Comma-separated trusted origins list.
    cors_origins: str = ""
    # JWT Settings
    jwt_secret_key: str
    jwt_algorithm: str = "HS256"
    jwt_access_token_expire_minutes: int = 60

    temp_path: str = "/tmp"

    # API Settings
    max_page_limit: int = Field(50, gt=0)
    allow_registration: bool = False
    root_path: str = "/"

    @property
    def authjwt(self):
        return {
            "authjwt_token_location": {"headers", "cookies"},
            "authjwt_secret_key": self.jwt_secret_key,
            "authjwt_algorithm": "HS256",
            "authjwt_access_token_expires": timedelta(minutes=self.jwt_access_token_expire_minutes),
            "authjwt_refresh_token_expires": timedelta(days=15),
            "authjwt_cookie_csrf_protect": False,
            # "authjwt_cookie_samesite": "lax",
        }.items()

    @property
    def normalized_root_path(self):
        return self.root_path[:-1] if self.root_path.endswith("/") else self.root_path

    @property
    def cors(self):
        return self.cors_origins.split(",")


@lru_cache(1)
def get_settings():
    logger.info("Loading config settings from the environment...")
    return Settings()
