from sqlalchemy import desc, select

from app.models.message import Message
from app.repositories.base import BaseRepository


class MessageRepository(BaseRepository):
    async def list_recent_by_conversation(self, conversation_id, limit: int = 10):
        return await self.list_all(
            select(Message)
            .where(Message.conversation_id == conversation_id)
            .order_by(desc(Message.created_at))
            .limit(limit)
        )
