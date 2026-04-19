from datetime import datetime
from uuid import UUID

from pydantic import BaseModel


class DatasetResponse(BaseModel):
    id: UUID
    owner_id: UUID
    name: str
    description: str | None
    file_type: str
    record_count: int
    status: str
    metadata_json: dict
    created_at: datetime
    updated_at: datetime

    model_config = {"from_attributes": True}
