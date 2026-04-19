from fastapi import APIRouter, Depends

from app.controllers.auth_controller import AuthController
from app.dependencies import get_auth_service
from app.schemas.auth import LoginRequest, RegisterRequest, TokenResponse, UserResponse
from app.schemas.common import SuccessResponse
from app.services.auth_service import AuthService

router = APIRouter(prefix="/auth", tags=["Authentication"])


def get_auth_controller(auth_service: AuthService = Depends(get_auth_service)):
    return AuthController(auth_service)


@router.post("/register", response_model=SuccessResponse[UserResponse])
async def register(payload: RegisterRequest, controller: AuthController = Depends(get_auth_controller)):
    return SuccessResponse(data=await controller.register(payload))


@router.post("/login", response_model=SuccessResponse[TokenResponse])
async def login(payload: LoginRequest, controller: AuthController = Depends(get_auth_controller)):
    return SuccessResponse(data=await controller.login(payload))
