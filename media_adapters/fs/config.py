from functools import lru_cache
from os import path

from pydantic import BaseSettings


class FilesystemSettings(BaseSettings):
    media_path: str

    def media(self, folder: str):
        return path.join(self.media_path, folder)


@lru_cache(1)
def get_settings():
    return FilesystemSettings()
