from sqlalchemy import select

from app.models.embedding_metadata import EmbeddingMetadata
from app.repositories.base import BaseRepository


class EmbeddingRepository(BaseRepository):
    async def get_by_dataset_id(self, dataset_id):
        return await self.get_one(
            select(EmbeddingMetadata).where(EmbeddingMetadata.dataset_id == dataset_id)
        )
