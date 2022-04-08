from shutil import rmtree

from aiofiles.os import makedirs
from aiofiles.os import wrap as async_wrap
from starlette.staticfiles import StaticFiles

from .config import get_settings
from .media import media

media_settings = get_settings()

rmtree = async_wrap(rmtree)


async def startup():
    """
    Removes lingering blobs.
    Creates folder structure.
    """
    await rmtree(media_settings.media("blobs"), ignore_errors=True)
    await makedirs(media_settings.media("users"), exist_ok=True)
    await makedirs(media_settings.media("blobs"), exist_ok=True)


async def shutdown():
    pass


mount = StaticFiles(directory=media_settings.media_path)
media = media
