from functools import lru_cache

from .config import DatabaseBackends, get_settings

global_settings = get_settings()


@lru_cache(1)
def get_backend():
    if global_settings.db_backend == DatabaseBackends.postgres:
        from db_adapters import postgres

        return postgres, postgres.models
    elif global_settings.db_backend == DatabaseBackends.deta:
        from db_adapters import deta

        return deta, deta.models
    else:
        raise ValueError(f"Unknown db backend {global_settings.db_backend}")


db, models = get_backend()
