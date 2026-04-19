import logging
from uuid import UUID

import socketio
from fastapi import FastAPI

from app.config.settings import get_settings
from app.db.session import AsyncSessionLocal
from app.repositories.conversation_repository import ConversationRepository
from app.repositories.dataset_repository import DatasetRepository
from app.repositories.embedding_repository import EmbeddingRepository
from app.repositories.message_repository import MessageRepository
from app.schemas.chat import ChatMessageRequest
from app.services.chat_service import ChatService
from app.services.dataset_service import DatasetService
from app.services.gemini_service import GeminiService
from app.services.vector_service import VectorService
from app.utils.cache import TTLCache
from app.utils.security import safe_decode_access_token

logger = logging.getLogger(__name__)
settings = get_settings()

sio = socketio.AsyncServer(
    async_mode="asgi",
    cors_allowed_origins=settings.socket_cors_origins,
)

cache = TTLCache()
gemini_service = GeminiService()
vector_service = VectorService(gemini_service)


@sio.event
async def connect(sid, environ, auth=None):
    token = (auth or {}).get("token")
    payload = safe_decode_access_token(token) if token else None
    if not payload:
        raise ConnectionRefusedError("Unauthorized")
    await sio.save_session(sid, {"user_id": payload["sub"]})
    logger.info("Socket connected | sid=%s | user_id=%s", sid, payload["sub"])


@sio.event
async def disconnect(sid):
    logger.info("Socket disconnected | sid=%s", sid)


@sio.event
async def typing_indicator(sid, data):
    await sio.emit("typing_indicator", data, skip_sid=sid)


@sio.event
async def error_event(sid, data):
    logger.error("Socket error event | sid=%s | data=%s", sid, data)


@sio.event
async def user_message(sid, data):
    session = await sio.get_session(sid)
    user_id = session["user_id"]
    await sio.emit("typing_indicator", {"status": "started"}, room=sid)

    try:
        async with AsyncSessionLocal() as db_session:
            dataset_repository = DatasetRepository(db_session)
            embedding_repository = EmbeddingRepository(db_session)
            dataset_service = DatasetService(dataset_repository, embedding_repository, vector_service)
            conversation_repository = ConversationRepository(db_session)
            message_repository = MessageRepository(db_session)
            chat_service = ChatService(
                conversation_repository=conversation_repository,
                message_repository=message_repository,
                dataset_service=dataset_service,
                vector_service=vector_service,
                gemini_service=gemini_service,
                cache=cache,
            )
            response = await chat_service.handle_chat(
                user_id=UUID(user_id),
                dataset_id=UUID(data["dataset_id"]),
                payload=ChatMessageRequest(
                    message=data["message"],
                    conversation_id=data.get("conversation_id"),
                ),
            )
            await sio.emit("bot_response", response.model_dump(mode="json"), room=sid)
    except Exception as exc:
        logger.exception("Socket chat processing failed", exc_info=exc)
        await sio.emit("error_event", {"message": str(exc)}, room=sid)
    finally:
        await sio.emit("typing_indicator", {"status": "stopped"}, room=sid)


def socket_app(fastapi_app: FastAPI):
    return socketio.ASGIApp(socketio_server=sio, other_asgi_app=fastapi_app)
