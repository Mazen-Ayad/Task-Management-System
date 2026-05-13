from typing import List
from fastapi import HTTPException
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.user import User
from app.repositories.user_repo import UserRepository
from app.schemas.user_schema import UserCreate, UserUpdate, UserResponse
from app.services.auth_service import hash_password
from app.utils.logger import get_logger

logger = get_logger(__name__)


class UserService:
    def __init__(self, db: AsyncSession):
        self.repo = UserRepository(db)

    async def create_user(self, data: UserCreate) -> UserResponse:
        if await self.repo.get_by_username(data.username):
            raise HTTPException(status_code=400, detail="Username already taken")
        if await self.repo.get_by_email(data.email):
            raise HTTPException(status_code=400, detail="Email already registered")

        user = User(
            username=data.username,
            email=data.email,
            full_name=data.full_name,
            hashed_password=hash_password(data.password),
            role=data.role,
        )
        user = await self.repo.create(user)
        logger.info(f"Created user: {user.username}")
        return UserResponse.model_validate(user)

    async def get_all_users(self) -> List[UserResponse]:
        users = await self.repo.get_all()
        return [UserResponse.model_validate(u) for u in users]

    async def get_user(self, user_id: int) -> UserResponse:
        user = await self.repo.get_by_id(user_id)
        if not user:
            raise HTTPException(status_code=404, detail="User not found")
        return UserResponse.model_validate(user)

    async def update_user(self, user_id: int, data: UserUpdate) -> UserResponse:
        user = await self.repo.get_by_id(user_id)
        if not user:
            raise HTTPException(status_code=404, detail="User not found")
        for field, value in data.model_dump(exclude_none=True).items():
            setattr(user, field, value)
        user = await self.repo.update(user)
        return UserResponse.model_validate(user)

    async def delete_user(self, user_id: int) -> dict:
        user = await self.repo.get_by_id(user_id)
        if not user:
            raise HTTPException(status_code=404, detail="User not found")
        await self.repo.delete(user)
        logger.info(f"Deleted user id={user_id}")
        return {"message": "User deleted"}