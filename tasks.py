from typing import List, Optional
from fastapi import APIRouter, Depends, Query
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.auth import get_current_user, require_roles
from app.database.session import get_db
from app.models.task import TaskStatus, TaskPriority
from app.models.user import UserRole
from app.schemas.task_schema import TaskCreate, TaskUpdate, TaskStatusUpdate, TaskResponse
from app.services.task_service import TaskService

router = APIRouter(prefix="/api/tasks", tags=["Tasks"])

admin_or_pm = require_roles(UserRole.admin, UserRole.project_manager)


@router.post("/", response_model=TaskResponse)
async def create_task(
    data: TaskCreate,
    db: AsyncSession = Depends(get_db),
    current_user=Depends(admin_or_pm),
):
    return await TaskService(db).create_task(data, current_user)


@router.get("/", response_model=List[TaskResponse])
async def list_tasks(
    project_id: Optional[int] = Query(None),
    status: Optional[TaskStatus] = Query(None),
    priority: Optional[TaskPriority] = Query(None),
    assignee_id: Optional[int] = Query(None),
    db: AsyncSession = Depends(get_db),
    current_user=Depends(get_current_user),
):
    return await TaskService(db).get_tasks(
        project_id=project_id,
        status=status,
        priority=priority,
        assignee_id=assignee_id,
        current_user=current_user,
    )


@router.get("/{task_id}", response_model=TaskResponse)
async def get_task(
    task_id: int,
    db: AsyncSession = Depends(get_db),
    _=Depends(get_current_user),
):
    return await TaskService(db).get_task(task_id)


@router.patch("/{task_id}", response_model=TaskResponse)
async def update_task(
    task_id: int,
    data: TaskUpdate,
    db: AsyncSession = Depends(get_db),
    current_user=Depends(get_current_user),
):
    return await TaskService(db).update_task(task_id, data, current_user)


@router.patch("/{task_id}/status", response_model=TaskResponse)
async def update_task_status(
    task_id: int,
    data: TaskStatusUpdate,
    db: AsyncSession = Depends(get_db),
    current_user=Depends(get_current_user),
):
    return await TaskService(db).update_task_status(task_id, data, current_user)


@router.delete("/{task_id}")
async def delete_task(
    task_id: int,
    db: AsyncSession = Depends(get_db),
    _=Depends(admin_or_pm),
):
    return await TaskService(db).delete_task(task_id)