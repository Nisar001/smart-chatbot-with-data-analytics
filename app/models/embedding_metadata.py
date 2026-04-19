import uuid

from sqlalchemy import Float, ForeignKey, Integer, String
from sqlalchemy.dialects.postgresql import JSONB, UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.models.base import Base, TimestampMixin


class EmbeddingMetadata(Base, TimestampMixin):
    __tablename__ = "embeddings_metadata"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    dataset_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("datasets.id"), index=True)
    faiss_index_path: Mapped[str] = mapped_column(String(500), nullable=False)
    chunk_count: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    embedding_dimension: Mapped[int] = mapped_column(Integer, default=768, nullable=False)
    model_name: Mapped[str] = mapped_column(String(120), nullable=False)
    processing_time_ms: Mapped[float] = mapped_column(Float, default=0.0, nullable=False)
    metadata_json: Mapped[dict] = mapped_column(JSONB, default=dict, nullable=False)

    dataset = relationship("Dataset", back_populates="embeddings")
