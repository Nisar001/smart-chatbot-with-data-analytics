import json
import logging
import os
from pathlib import Path
from uuid import UUID

from fastapi import HTTPException, UploadFile, status

from app.config.settings import get_settings
from app.models.dataset import Dataset
from app.models.embedding_metadata import EmbeddingMetadata
from app.repositories.dataset_repository import DatasetRepository
from app.repositories.embedding_repository import EmbeddingRepository
from app.schemas.dataset import DatasetResponse
from app.services.vector_service import VectorService
from app.utils.document_builder import records_to_documents
from app.utils.file_parser import parse_upload

logger = logging.getLogger(__name__)
settings = get_settings()


class DatasetService:
    def __init__(
        self,
        dataset_repository: DatasetRepository,
        embedding_repository: EmbeddingRepository,
        vector_service: VectorService,
    ):
        self.dataset_repository = dataset_repository
        self.embedding_repository = embedding_repository
        self.vector_service = vector_service
        Path(settings.upload_dir).mkdir(parents=True, exist_ok=True)

    async def upload_and_process(
        self,
        user_id: UUID,
        name: str,
        description: str | None,
        file: UploadFile,
    ) -> DatasetResponse:
        rows, file_type = await parse_upload(file)
        if not rows:
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Uploaded dataset is empty.")

        dataset = Dataset(
            owner_id=user_id,
            name=name,
            description=description,
            file_path="",
            file_type=file_type,
            record_count=len(rows),
            status="processing",
            metadata_json={"original_filename": file.filename},
        )
        await self.dataset_repository.add(dataset)
        await self.dataset_repository.session.flush()

        file_path = os.path.join(settings.upload_dir, f"{dataset.id}.{file_type}")
        with open(file_path, "w", encoding="utf-8") as file_pointer:
            json.dump(rows, file_pointer, ensure_ascii=True, indent=2)
        dataset.file_path = file_path

        documents = records_to_documents(name, rows)
        index_path, chunk_count, embedding_dimension, processing_time_ms, model_name = await self.vector_service.create_index(
            dataset.id, documents
        )

        embedding_metadata = await self.embedding_repository.get_by_dataset_id(dataset.id)
        if embedding_metadata is None:
            embedding_metadata = EmbeddingMetadata(
                dataset_id=dataset.id,
                faiss_index_path=index_path,
                chunk_count=chunk_count,
                embedding_dimension=embedding_dimension,
                model_name=model_name,
                processing_time_ms=processing_time_ms,
                metadata_json={"batch_embedding_size": settings.batch_embedding_size},
            )
            await self.embedding_repository.add(embedding_metadata)

        dataset.status = "ready"
        dataset.metadata_json = {
            **dataset.metadata_json,
            "chunk_count": chunk_count,
            "embedding_dimension": embedding_dimension,
            "embedding_model": model_name,
        }

        await self.dataset_repository.session.commit()
        await self.dataset_repository.session.refresh(dataset)
        logger.info("Dataset processed successfully | dataset_id=%s", dataset.id)
        return DatasetResponse.model_validate(dataset)

    async def list_user_datasets(self, user_id: UUID) -> list[DatasetResponse]:
        datasets = await self.dataset_repository.list_by_owner(user_id)
        return [DatasetResponse.model_validate(item) for item in datasets]

    async def validate_dataset_access(self, dataset_id: UUID, user_id: UUID) -> Dataset:
        dataset = await self.dataset_repository.get_by_id(dataset_id)
        if not dataset or dataset.owner_id != user_id:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Dataset not found.")
        if dataset.status != "ready":
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail="Dataset is not ready for querying.",
            )
        return dataset
