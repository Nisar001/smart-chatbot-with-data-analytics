from sqlalchemy import select
from sqlalchemy.orm import selectinload

from app.models.conversation import Conversation
from app.repositories.base import BaseRepository


class ConversationRepository(BaseRepository):
    async def get_by_id(self, conversation_id):
        return await self.get_one(
            select(Conversation)
            .options(selectinload(Conversation.messages))
            .where(Conversation.id == conversation_id)
        )

    async def list_by_user(self, user_id):
        return await self.list_all(
            select(Conversation)
            .options(selectinload(Conversation.messages))
            .where(Conversation.user_id == user_id)
            .order_by(Conversation.updated_at.desc())
        )
