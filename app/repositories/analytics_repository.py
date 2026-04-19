from sqlalchemy import func, select

from app.models.conversation import Conversation
from app.models.dataset import Dataset
from app.models.message import Message
from app.repositories.base import BaseRepository


class AnalyticsRepository(BaseRepository):
    async def most_asked_queries(self, limit: int = 5):
        statement = (
            select(Message.content, func.count(Message.id).label("query_count"))
            .where(Message.role == "user")
            .group_by(Message.content)
            .order_by(func.count(Message.id).desc())
            .limit(limit)
        )
        result = await self.session.execute(statement)
        return result.all()

    async def dataset_usage_stats(self):
        statement = (
            select(
                Dataset.id,
                Dataset.name,
                func.count(Conversation.id).label("conversation_count"),
            )
            .outerjoin(Conversation, Conversation.dataset_id == Dataset.id)
            .group_by(Dataset.id, Dataset.name)
            .order_by(func.count(Conversation.id).desc())
        )
        result = await self.session.execute(statement)
        return result.all()

    async def latency_stats(self):
        statement = select(
            func.avg(Message.latency_ms),
            func.max(Message.latency_ms),
            func.min(Message.latency_ms),
        ).where(Message.role == "assistant", Message.latency_ms.is_not(None))
        result = await self.session.execute(statement)
        return result.one()
