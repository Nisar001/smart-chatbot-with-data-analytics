from datetime import datetime
from uuid import UUID

from pydantic import BaseModel, Field


class ChatMessageRequest(BaseModel):
    message: str = Field(min_length=1, max_length=4000)
    conversation_id: UUID | None = None


class SourceChunk(BaseModel):
    page_content: str
    metadata: dict


class ChatResponse(BaseModel):
    conversation_id: UUID
    user_message_id: UUID
    assistant_message_id: UUID
    response: str
    latency_ms: float
    sources: list[SourceChunk]


class MessageResponse(BaseModel):
    id: UUID
    role: str
    content: str
    latency_ms: float | None
    metadata_json: dict
    created_at: datetime

    model_config = {"from_attributes": True}


class ConversationResponse(BaseModel):
    id: UUID
    dataset_id: UUID
    title: str
    status: str
    metadata_json: dict
    created_at: datetime
    updated_at: datetime
    messages: list[MessageResponse] = []

    model_config = {"from_attributes": True}
