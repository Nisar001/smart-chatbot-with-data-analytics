from uuid import UUID

from app.schemas.chat import ChatMessageRequest, ChatResponse, ConversationResponse
from app.services.chat_service import ChatService


class ChatController:
    def __init__(self, chat_service: ChatService):
        self.chat_service = chat_service

    async def send_message(
        self, user_id: UUID, dataset_id: UUID, payload: ChatMessageRequest
    ) -> ChatResponse:
        return await self.chat_service.handle_chat(user_id=user_id, dataset_id=dataset_id, payload=payload)

    async def list_conversations(self, user_id: UUID) -> list[ConversationResponse]:
        return await self.chat_service.list_conversations(user_id)
