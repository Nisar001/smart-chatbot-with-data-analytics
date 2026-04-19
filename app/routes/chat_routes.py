from uuid import UUID

from fastapi import APIRouter, Depends

from app.controllers.chat_controller import ChatController
from app.dependencies import get_chat_service, get_current_user
from app.models.user import User
from app.schemas.chat import ChatMessageRequest, ChatResponse, ConversationResponse
from app.schemas.common import SuccessResponse
from app.services.chat_service import ChatService

router = APIRouter(prefix="/chat", tags=["Chat"])


def get_chat_controller(chat_service: ChatService = Depends(get_chat_service)):
    return ChatController(chat_service)


@router.post("/{dataset_id}/message", response_model=SuccessResponse[ChatResponse])
async def send_message(
    dataset_id: UUID,
    payload: ChatMessageRequest,
    current_user: User = Depends(get_current_user),
    controller: ChatController = Depends(get_chat_controller),
):
    return SuccessResponse(data=await controller.send_message(current_user.id, dataset_id, payload))


@router.get("/conversations", response_model=SuccessResponse[list[ConversationResponse]])
async def list_conversations(
    current_user: User = Depends(get_current_user),
    controller: ChatController = Depends(get_chat_controller),
):
    return SuccessResponse(data=await controller.list_conversations(current_user.id))
