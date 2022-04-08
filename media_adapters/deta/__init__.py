from .config import get_settings
from .media import media
from .mount import mount

media_settings = get_settings()


async def startup():
    """
    Removes lingering blobs.
    """
    media.rmtree("blobs")


async def shutdown():
    pass


mount = mount
media = media
