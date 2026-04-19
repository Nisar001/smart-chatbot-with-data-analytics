from datetime import datetime, timezone
from types import SimpleNamespace
from unittest.mock import AsyncMock

import pytest
from fastapi import HTTPException

from app.schemas.auth import LoginRequest, RegisterRequest
from app.services.auth_service import AuthService
from app.utils.security import hash_password


@pytest.mark.asyncio
async def test_register_creates_user():
    session = SimpleNamespace(commit=AsyncMock(), refresh=AsyncMock())
    async def add_side_effect(user):
        user.id = "0f0b6b1d-6d6a-48e8-8538-c2c7fb690001"
        user.created_at = datetime.now(timezone.utc)
        user.is_active = True
        return user

    repository = SimpleNamespace(
        get_by_email=AsyncMock(return_value=None),
        add=AsyncMock(side_effect=add_side_effect),
        session=session,
    )
    service = AuthService(repository)

    result = await service.register(
        RegisterRequest(
            email="demo@example.com",
            full_name="Demo User",
            password="supersecurepassword",
        )
    )

    assert result.email == "demo@example.com"
    repository.add.assert_awaited_once()
    session.commit.assert_awaited_once()


@pytest.mark.asyncio
async def test_login_rejects_invalid_password():
    repository = SimpleNamespace(
        get_by_email=AsyncMock(
            return_value=SimpleNamespace(
                id="123",
                email="demo@example.com",
                full_name="Demo User",
                password_hash=hash_password("correct-password"),
                is_active=True,
                created_at="2026-01-01T00:00:00Z",
            )
        )
    )
    service = AuthService(repository)

    with pytest.raises(HTTPException) as exc:
        await service.login(
            LoginRequest(email="demo@example.com", password="wrong-password1")
        )

    assert exc.value.status_code == 401
