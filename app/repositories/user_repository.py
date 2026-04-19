from sqlalchemy import select

from app.models.user import User
from app.repositories.base import BaseRepository


class UserRepository(BaseRepository):
    async def get_by_email(self, email: str) -> User | None:
        return await self.get_one(select(User).where(User.email == email))

    async def get_by_id(self, user_id):
        return await self.get_one(select(User).where(User.id == user_id))
