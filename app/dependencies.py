from uuid import UUID

from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.session import get_db_session
from app.repositories.analytics_repository import AnalyticsRepository
from app.repositories.conversation_repository import ConversationRepository
from app.repositories.dataset_repository import DatasetRepository
from app.repositories.embedding_repository import EmbeddingRepository
from app.repositories.message_repository import MessageRepository
from app.repositories.user_repository import UserRepository
from app.services.analytics_service import AnalyticsService
from app.services.auth_service import AuthService
from app.services.chat_service import ChatService
from app.services.dataset_service import DatasetService
from app.services.gemini_service import GeminiService
from app.services.vector_service import VectorService
from app.utils.cache import TTLCache
from app.utils.security import safe_decode_access_token

bearer_scheme = HTTPBearer()
cache_instance = TTLCache()
gemini_service = GeminiService()
vector_service = VectorService(gemini_service)


def get_user_repository(session: AsyncSession = Depends(get_db_session)):
    return UserRepository(session)


def get_dataset_repository(session: AsyncSession = Depends(get_db_session)):
    return DatasetRepository(session)


def get_embedding_repository(session: AsyncSession = Depends(get_db_session)):
    return EmbeddingRepository(session)


def get_conversation_repository(session: AsyncSession = Depends(get_db_session)):
    return ConversationRepository(session)


def get_message_repository(session: AsyncSession = Depends(get_db_session)):
    return MessageRepository(session)


def get_analytics_repository(session: AsyncSession = Depends(get_db_session)):
    return AnalyticsRepository(session)


def get_auth_service(user_repository: UserRepository = Depends(get_user_repository)):
    return AuthService(user_repository)


def get_dataset_service(
    dataset_repository: DatasetRepository = Depends(get_dataset_repository),
    embedding_repository: EmbeddingRepository = Depends(get_embedding_repository),
):
    return DatasetService(dataset_repository, embedding_repository, vector_service)


def get_chat_service(
    conversation_repository: ConversationRepository = Depends(get_conversation_repository),
    message_repository: MessageRepository = Depends(get_message_repository),
    dataset_service: DatasetService = Depends(get_dataset_service),
):
    return ChatService(
        conversation_repository=conversation_repository,
        message_repository=message_repository,
        dataset_service=dataset_service,
        vector_service=vector_service,
        gemini_service=gemini_service,
        cache=cache_instance,
    )


def get_analytics_service(
    analytics_repository: AnalyticsRepository = Depends(get_analytics_repository),
):
    return AnalyticsService(analytics_repository)


async def get_current_user(
    credentials: HTTPAuthorizationCredentials = Depends(bearer_scheme),
    user_repository: UserRepository = Depends(get_user_repository),
):
    payload = safe_decode_access_token(credentials.credentials)
    if not payload or "sub" not in payload:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid or expired token.")
    try:
        user_id = UUID(payload["sub"])
    except ValueError as exc:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid token subject.") from exc
    user = await user_repository.get_by_id(user_id)
    if not user:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="User not found.")
    return user
