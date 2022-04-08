from functools import lru_cache

from pydantic import BaseSettings


class PostgresSettings(BaseSettings):
    pg_host: str
    pg_user: str
    pg_pass: str
    pg_db: str

    @property
    def url(self):
        return f"postgresql+asyncpg://{self.pg_user}:{self.pg_pass}@{self.pg_host}/{self.pg_db}"


@lru_cache(1)
def get_settings():
    return PostgresSettings()
