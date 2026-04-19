from app.schemas.auth import LoginRequest, RegisterRequest, TokenResponse, UserResponse
from app.services.auth_service import AuthService


class AuthController:
    def __init__(self, auth_service: AuthService):
        self.auth_service = auth_service

    async def register(self, payload: RegisterRequest) -> UserResponse:
        return await self.auth_service.register(payload)

    async def login(self, payload: LoginRequest) -> TokenResponse:
        return await self.auth_service.login(payload)
