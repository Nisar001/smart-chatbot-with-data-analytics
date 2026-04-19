from uuid import UUID

from fastapi import UploadFile

from app.schemas.dataset import DatasetResponse
from app.services.dataset_service import DatasetService


class DatasetController:
    def __init__(self, dataset_service: DatasetService):
        self.dataset_service = dataset_service

    async def upload_dataset(
        self, user_id: UUID, name: str, description: str | None, file: UploadFile
    ) -> DatasetResponse:
        return await self.dataset_service.upload_and_process(
            user_id=user_id,
            name=name,
            description=description,
            file=file,
        )

    async def list_datasets(self, user_id: UUID) -> list[DatasetResponse]:
        return await self.dataset_service.list_user_datasets(user_id)
