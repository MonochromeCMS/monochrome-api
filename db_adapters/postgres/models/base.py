import uuid

from fastapi import HTTPException
from sqlalchemy import Column, Integer, func, select
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.ext.declarative import as_declarative, declared_attr

ErrorException = HTTPException(422, "Database error")

NotFoundException = HTTPException(404, "Resource not found")


@as_declarative()
class Base:
    __name__: str
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    version = Column(Integer, default=0)

    @declared_attr
    def __mapper_args__(cls):
        return {"eager_defaults": True}

    # Generate __tablename__ automatically
    @declared_attr
    def __tablename__(cls) -> str:
        return cls.__name__.lower()

    async def save(self, db_session: AsyncSession):
        """
        Saves this instance on db.
        The session comes from `db_session` on `session.py`
        """
        try:
            self.version = self.version + 1 if self.version else 1
            db_session.add(self)

            await db_session.commit()
        except SQLAlchemyError:
            raise ErrorException

        return self

    async def delete(self, db_session: AsyncSession):
        """
        Deletes this instance, it'll error out if it can't be found in the database.
        The session comes from `db_session` on `session.py`
        """
        try:
            await db_session.delete(self)
        except SQLAlchemyError:
            raise ErrorException

        return "OK"

    async def update(self, db_session: AsyncSession, **kwargs):
        """
        Update fields on this instance, equivalent to changing the fields manually and saving.
        The session comes from `db_session` on `session.py`
        """
        for k, v in kwargs.items():
            setattr(self, k, v)
        await self.save(db_session)

        return self

    @classmethod
    async def find(cls, db_session: AsyncSession, id: uuid.UUID, exception=NotFoundException):
        """
        Returns the instance whose id is provided.
        """
        stmt = select(cls).where(cls.id == id)
        result = await db_session.execute(stmt)
        instance = result.scalars().first()
        if instance is None:
            if exception:
                raise exception
            return None
        else:
            return instance

    @classmethod
    async def _pagination(cls, db_session, stmt, limit, offset, order_by):
        """
        Returns a paginated version of an existing query (`stmt`) in the order requested.
        """
        count_stmt = stmt.with_only_columns(func.count(cls.id))
        count_result = await db_session.execute(count_stmt)
        page_stmt = stmt.order_by(*order_by).offset(offset).limit(limit)
        page_result = await db_session.execute(page_stmt)
        return count_result.scalars().first(), page_result.unique().scalars().all()
