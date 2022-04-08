from functools import lru_cache

from pydantic import BaseSettings


class DetaMediaSettings(BaseSettings):
    deta_project_key: str


@lru_cache(1)
def get_settings():
    return DetaMediaSettings()
