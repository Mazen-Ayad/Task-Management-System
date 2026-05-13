from typing import List
from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.auth import get_current_user, require_roles
from app.database.session import get_db
from app.models.user import UserRole
from app.schemas.project_schema import ProjectCreate, ProjectUpdate, ProjectResponse
from app.services.project_service import ProjectService

router = APIRouter(prefix="/api/projects", tags=["Projects"])

admin_only = require_roles(UserRole.admin)
admin_or_pm = require_roles(UserRole.admin, UserRole.project_manager)


@router.post("/", response_model=ProjectResponse)
async def create_project(
    data: ProjectCreate,
    db: AsyncSession = Depends(get_db),
    current_user=Depends(admin_or_pm),
):
    return await ProjectService(db).create_project(data, current_user.id)


@router.get("/", response_model=List[ProjectResponse])
async def list_projects(
    db: AsyncSession = Depends(get_db),
    _=Depends(get_current_user),          # ← all roles can read
):
    return await ProjectService(db).get_all_projects()


@router.get("/{project_id}", response_model=ProjectResponse)
async def get_project(
    project_id: int,
    db: AsyncSession = Depends(get_db),
    _=Depends(get_current_user),          # ← all roles can read
):
    return await ProjectService(db).get_project(project_id)


@router.patch("/{project_id}", response_model=ProjectResponse)
async def update_project(
    project_id: int,
    data: ProjectUpdate,
    db: AsyncSession = Depends(get_db),
    current_user=Depends(admin_or_pm),
):
    return await ProjectService(db).update_project(project_id, data, current_user)


@router.delete("/{project_id}")
async def delete_project(
    project_id: int,
    db: AsyncSession = Depends(get_db),
    _=Depends(admin_only),
):
    return await ProjectService(db).delete_project(project_id)