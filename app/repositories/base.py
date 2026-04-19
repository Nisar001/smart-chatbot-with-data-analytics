from sqlalchemy import Select, select
from sqlalchemy.ext.asyncio import AsyncSession


class BaseRepository:
    def __init__(self, session: AsyncSession):
        self.session = session

    async def add(self, entity):
        self.session.add(entity)
        await self.session.flush()
        return entity

    async def get_one(self, statement: Select):
        result = await self.session.execute(statement)
        return result.scalar_one_or_none()

    async def list_all(self, statement: Select):
        result = await self.session.execute(statement)
        return list(result.scalars().all())

    def select(self, model):
        return select(model)
