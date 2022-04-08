from functools import lru_cache

from .config import MediaBackends, get_settings

global_settings = get_settings()


@lru_cache(1)
def get_backend():
    if global_settings.media_backend == MediaBackends.filesystem:
        from media_adapters import fs

        return fs
    elif global_settings.media_backend == MediaBackends.deta:
        from media_adapters import deta

        return deta
    else:
        raise ValueError(f"Unknown media backend {global_settings.db_backend}")


media = get_backend()
