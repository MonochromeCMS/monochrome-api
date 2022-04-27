from contextlib import asynccontextmanager
from math import inf
from typing import ClassVar
from uuid import UUID, uuid4

from deta import Deta
from fastapi import HTTPException
from fastapi.encoders import jsonable_encoder
from pydantic import BaseModel, Field

from ..config import get_settings

settings = get_settings()

ErrorException = HTTPException(422, "Database error")

NotFoundException = HTTPException(404, "Resource not found")


@asynccontextmanager
async def async_client(deta: Deta, db_name: str):
    try:
        client = deta.AsyncBase(db_name)
        yield client
    except:
        raise ErrorException
    finally:
        await client.close()


class Base(BaseModel):
    id: UUID = Field(default_factory=uuid4)
    version: int = 0
    db_name: ClassVar

    def dict(self, *args, **kwargs):
        return {**super().dict(*args, **kwargs), "key": str(self.id)}

    async def save(self, db_session: Deta):
        """
        Saves this instance on db.
        The session comes from `db_session` on `session.py`
        """
        async with async_client(db_session, self.db_name) as db:
            self.version += 1
            await db.put(jsonable_encoder(self))

    async def delete(self, db_session: Deta):
        """
        Deletes this instance.
        The session comes from `db_session` on `session.py`
        """
        async with async_client(db_session, self.db_name) as db:
            await db.delete(str(self.id))
        return "OK"

    async def update(self, db_session: Deta, **kwargs):
        """
        Update fields on this instance, equivalent to changing the fields manually and saving.
        The session comes from `db_session` on `session.py`
        """
        new_dict = {**self.dict(), **kwargs}
        new_instance = self.__class__(**new_dict)
        await new_instance.save(db_session)

        self.__dict__.update(new_instance.__dict__)

    @classmethod
    async def find(cls, db_session: Deta, id: UUID, exception=NotFoundException):
        """
        Returns the instance whose id is provided.
        """
        async with async_client(db_session, cls.db_name) as db:
            instance = await db.get(str(id))

        if instance is None:
            if exception:
                raise exception
            return None
        else:
            return cls(**instance)

    @classmethod
    async def _fetch(cls, db_session, query, limit: int = inf):
        async with async_client(db_session, cls.db_name) as db:
            query = jsonable_encoder(query)
            res = await db.fetch(query, limit=min(limit, 100))
            all_items = res.items

            while len(all_items) <= limit and res.last:
                res = await db.fetch(query, last=res.last)
                all_items += res.items

            return [cls(**instance) for instance in all_items]

    @classmethod
    async def _pagination(cls, db_session, query, limit, offset, order_by, reverse=False):
        if query is None:
            query = dict()
        results = await cls._fetch(db_session, query)
        count = len(results)
        page = sorted(results, key=order_by, reverse=reverse)[offset : offset + limit]
        return count, page
