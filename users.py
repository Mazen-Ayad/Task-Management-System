from typing import List
from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.auth import get_current_user, require_roles
from app.database.session import get_db
from app.models.user import UserRole
from app.schemas.user_schema import UserCreate, UserUpdate, UserResponse
from app.services.user_service import UserService

router = APIRouter(prefix="/api/users", tags=["Users"])

admin_only = require_roles(UserRole.admin)


@router.post("/", response_model=UserResponse)
async def create_user(
    data: UserCreate,
    db: AsyncSession = Depends(get_db),
    _=Depends(admin_only),
):
    """Admin only: create a new user."""
    return await UserService(db).create_user(data)


@router.get("/", response_model=List[UserResponse])
async def list_users(
    db: AsyncSession = Depends(get_db),
    current_user=Depends(get_current_user),
):
    return await UserService(db).get_all_users()


@router.get("/me", response_model=UserResponse)
async def get_me(current_user=Depends(get_current_user)):
    from app.schemas.user_schema import UserResponse
    return UserResponse.model_validate(current_user)


@router.get("/{user_id}", response_model=UserResponse)
async def get_user(
    user_id: int,
    db: AsyncSession = Depends(get_db),
    _=Depends(get_current_user),
):
    return await UserService(db).get_user(user_id)


@router.patch("/{user_id}", response_model=UserResponse)
async def update_user(
    user_id: int,
    data: UserUpdate,
    db: AsyncSession = Depends(get_db),
    _=Depends(admin_only),
):
    return await UserService(db).update_user(user_id, data)


@router.delete("/{user_id}")
async def delete_user(
    user_id: int,
    db: AsyncSession = Depends(get_db),
    _=Depends(admin_only),
):
    return await UserService(db).delete_user(user_id)