from fastapi import HTTPException, status

from app.models.user import User
from app.repositories.user_repository import UserRepository
from app.schemas.auth import LoginRequest, RegisterRequest, TokenResponse, UserResponse
from app.utils.security import create_access_token, hash_password, verify_password


class AuthService:
    def __init__(self, user_repository: UserRepository):
        self.user_repository = user_repository

    async def register(self, payload: RegisterRequest) -> UserResponse:
        existing_user = await self.user_repository.get_by_email(payload.email)
        if existing_user:
            raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="Email already registered.")

        user = User(
            email=payload.email,
            full_name=payload.full_name,
            password_hash=hash_password(payload.password),
        )
        await self.user_repository.add(user)
        await self.user_repository.session.commit()
        await self.user_repository.session.refresh(user)
        return UserResponse.model_validate(user)

    async def login(self, payload: LoginRequest) -> TokenResponse:
        user = await self.user_repository.get_by_email(payload.email)
        if not user or not verify_password(payload.password, user.password_hash):
            raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid credentials.")

        token = create_access_token(str(user.id))
        return TokenResponse(access_token=token, user=UserResponse.model_validate(user))
