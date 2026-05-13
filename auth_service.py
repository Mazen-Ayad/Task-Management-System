from fastapi import HTTPException, status
import bcrypt
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.auth import create_access_token
from app.repositories.user_repo import UserRepository
from app.schemas.auth_schema import TokenResponse
from app.utils.logger import get_logger

logger = get_logger(__name__)


def hash_password(password: str) -> str:
    return bcrypt.hashpw(password.encode("utf-8"), bcrypt.gensalt()).decode("utf-8")


def verify_password(plain: str, hashed: str) -> bool:
    return bcrypt.checkpw(plain.encode("utf-8"), hashed.encode("utf-8"))


class AuthService:
    def __init__(self, db: AsyncSession):
        self.repo = UserRepository(db)

    async def login(self, username: str, password: str) -> TokenResponse:
        user = await self.repo.get_by_username(username)
        if not user or not verify_password(password, user.hashed_password):
            logger.warning(f"Failed login attempt for username: {username}")
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid username or password",
            )
        if not user.is_active:
            raise HTTPException(status_code=403, detail="Account is inactive")

        token = create_access_token({"sub": str(user.id)})
        logger.info(f"User {username} logged in successfully")
        return TokenResponse(
            access_token=token,
            token_type="bearer",
            user_id=user.id,
            username=user.username,
            role=user.role,
        )