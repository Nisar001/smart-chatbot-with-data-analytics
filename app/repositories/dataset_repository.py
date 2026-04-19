from sqlalchemy import select

from app.models.dataset import Dataset
from app.repositories.base import BaseRepository


class DatasetRepository(BaseRepository):
    async def get_by_id(self, dataset_id):
        return await self.get_one(select(Dataset).where(Dataset.id == dataset_id))

    async def list_by_owner(self, owner_id):
        return await self.list_all(
            select(Dataset).where(Dataset.owner_id == owner_id).order_by(Dataset.created_at.desc())
        )
