import logging
import time
from uuid import UUID, uuid4

from fastapi import HTTPException, status

from app.config.settings import get_settings
from app.models.conversation import Conversation
from app.models.message import Message
from app.repositories.conversation_repository import ConversationRepository
from app.repositories.message_repository import MessageRepository
from app.schemas.chat import ChatMessageRequest, ChatResponse, ConversationResponse, SourceChunk
from app.services.dataset_service import DatasetService
from app.services.gemini_service import GeminiService
from app.services.vector_service import VectorService
from app.utils.cache import TTLCache

logger = logging.getLogger(__name__)
settings = get_settings()


class ChatService:
    def __init__(
        self,
        conversation_repository: ConversationRepository,
        message_repository: MessageRepository,
        dataset_service: DatasetService,
        vector_service: VectorService,
        gemini_service: GeminiService,
        cache: TTLCache,
    ):
        self.conversation_repository = conversation_repository
        self.message_repository = message_repository
        self.dataset_service = dataset_service
        self.vector_service = vector_service
        self.gemini_service = gemini_service
        self.cache = cache

    async def handle_chat(self, user_id: UUID, dataset_id: UUID, payload: ChatMessageRequest) -> ChatResponse:
        dataset = await self.dataset_service.validate_dataset_access(dataset_id, user_id)
        conversation = await self._get_or_create_conversation(payload.conversation_id, user_id, dataset_id, payload.message)

        user_message = Message(
            id=uuid4(),
            conversation_id=conversation.id,
            role="user",
            content=payload.message,
            metadata_json={"dataset_id": str(dataset_id)},
        )
        await self.message_repository.add(user_message)

        cache_key = f"{dataset_id}:{payload.message.strip().lower()}"
        cached = await self.cache.get(cache_key) if settings.enable_cache else None
        if cached:
            latency_ms = 0.0
            response_text = cached["response"]
            sources = cached["sources"]
        else:
            started_at = time.perf_counter()
            source_documents = await self.vector_service.retrieve(dataset_id, payload.message)
            prompt = await self._build_prompt(conversation.id, dataset.name, payload.message, source_documents)
            response_text = await self.gemini_service.generate_answer(prompt)
            latency_ms = (time.perf_counter() - started_at) * 1000
            sources = [
                SourceChunk(page_content=document.page_content, metadata=document.metadata)
                for document in source_documents
            ]
            if settings.enable_cache:
                await self.cache.set(
                    cache_key,
                    {
                        "response": response_text,
                        "sources": sources,
                    },
                    settings.cache_ttl_seconds,
                )

        assistant_message = Message(
            id=uuid4(),
            conversation_id=conversation.id,
            role="assistant",
            content=response_text,
            latency_ms=latency_ms,
            metadata_json={
                "dataset_id": str(dataset_id),
                "cached": bool(cached),
                "latency_threshold_exceeded": latency_ms > settings.default_latency_threshold_ms,
            },
        )
        await self.message_repository.add(assistant_message)
        await self.message_repository.session.commit()
        return ChatResponse(
            conversation_id=conversation.id,
            user_message_id=user_message.id,
            assistant_message_id=assistant_message.id,
            response=response_text,
            latency_ms=latency_ms,
            sources=sources,
        )

    async def list_conversations(self, user_id: UUID) -> list[ConversationResponse]:
        conversations = await self.conversation_repository.list_by_user(user_id)
        return [ConversationResponse.model_validate(item) for item in conversations]

    async def _get_or_create_conversation(
        self,
        conversation_id: UUID | None,
        user_id: UUID,
        dataset_id: UUID,
        initial_message: str,
    ) -> Conversation:
        if conversation_id:
            conversation = await self.conversation_repository.get_by_id(conversation_id)
            if not conversation or conversation.user_id != user_id:
                raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Conversation not found.")
            return conversation

        conversation = Conversation(
            user_id=user_id,
            dataset_id=dataset_id,
            title=initial_message[:80],
            metadata_json={},
        )
        await self.conversation_repository.add(conversation)
        await self.conversation_repository.session.flush()
        return conversation

    async def _build_prompt(self, conversation_id: UUID, dataset_name: str, message: str, source_documents):
        recent_messages = await self.message_repository.list_recent_by_conversation(conversation_id, limit=6)
        history = "\n".join(
            f"{msg.role.upper()}: {msg.content}"
            for msg in reversed(recent_messages)
        )
        context = "\n\n".join(doc.page_content for doc in source_documents)
        return f"""
You are a data assistant for the dataset "{dataset_name}".
Answer only from the retrieved context and the user conversation history.
If the answer is not in context, explicitly say that the dataset does not provide enough information.
Keep the answer concise, explainable, and business-friendly.

Conversation history:
{history}

Retrieved context:
{context}

User question:
{message}

Return:
1. Direct answer
2. Short explanation of how the answer was derived from the dataset
3. Mention any uncertainty
""".strip()
