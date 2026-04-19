from types import SimpleNamespace
from unittest.mock import AsyncMock
from uuid import uuid4

import pytest
from langchain_core.documents import Document

from app.schemas.chat import ChatMessageRequest, SourceChunk
from app.services.chat_service import ChatService
from app.utils.cache import TTLCache


@pytest.mark.asyncio
async def test_chat_service_uses_cached_answer():
    user_id = uuid4()
    dataset_id = uuid4()
    conversation_id = uuid4()
    cache = TTLCache()
    cached_sources = [SourceChunk(page_content="sales: 100", metadata={"row_index": 0})]
    await cache.set(
        f"{dataset_id}:what is the sales total?",
        {"response": "Total sales are 100.", "sources": cached_sources},
        300,
    )

    conversation_repository = SimpleNamespace(
        get_by_id=AsyncMock(
            return_value=SimpleNamespace(id=conversation_id, user_id=user_id)
        ),
        add=AsyncMock(),
        session=SimpleNamespace(flush=AsyncMock()),
    )
    message_repository = SimpleNamespace(
        add=AsyncMock(),
        list_recent_by_conversation=AsyncMock(return_value=[]),
        session=SimpleNamespace(commit=AsyncMock()),
    )
    dataset_service = SimpleNamespace(
        validate_dataset_access=AsyncMock(return_value=SimpleNamespace(id=dataset_id, name="Sales"))
    )
    vector_service = SimpleNamespace(retrieve=AsyncMock(return_value=[Document(page_content="unused", metadata={})]))
    gemini_service = SimpleNamespace(generate_answer=AsyncMock(return_value="Should not be used"))

    service = ChatService(
        conversation_repository=conversation_repository,
        message_repository=message_repository,
        dataset_service=dataset_service,
        vector_service=vector_service,
        gemini_service=gemini_service,
        cache=cache,
    )

    response = await service.handle_chat(
        user_id=user_id,
        dataset_id=dataset_id,
        payload=ChatMessageRequest(
            message="What is the sales total?",
            conversation_id=conversation_id,
        ),
    )

    assert response.response == "Total sales are 100."
    assert response.latency_ms == 0.0
    gemini_service.generate_answer.assert_not_called()


@pytest.mark.asyncio
async def test_chat_service_calls_llm_on_cache_miss():
    user_id = uuid4()
    dataset_id = uuid4()
    conversation = SimpleNamespace(id=uuid4(), user_id=user_id)

    conversation_repository = SimpleNamespace(
        get_by_id=AsyncMock(return_value=conversation),
        add=AsyncMock(),
        session=SimpleNamespace(flush=AsyncMock()),
    )
    message_repository = SimpleNamespace(
        add=AsyncMock(),
        list_recent_by_conversation=AsyncMock(return_value=[]),
        session=SimpleNamespace(commit=AsyncMock()),
    )
    dataset_service = SimpleNamespace(
        validate_dataset_access=AsyncMock(return_value=SimpleNamespace(id=dataset_id, name="Support"))
    )
    vector_service = SimpleNamespace(
        retrieve=AsyncMock(return_value=[Document(page_content="status: resolved", metadata={"row_index": 1})])
    )
    gemini_service = SimpleNamespace(generate_answer=AsyncMock(return_value="The issue is resolved."))

    service = ChatService(
        conversation_repository=conversation_repository,
        message_repository=message_repository,
        dataset_service=dataset_service,
        vector_service=vector_service,
        gemini_service=gemini_service,
        cache=TTLCache(),
    )

    response = await service.handle_chat(
        user_id=user_id,
        dataset_id=dataset_id,
        payload=ChatMessageRequest(message="What is the current status?", conversation_id=conversation.id),
    )

    assert response.response == "The issue is resolved."
    gemini_service.generate_answer.assert_awaited_once()
