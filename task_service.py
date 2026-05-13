from typing import List, Optional
from fastapi import HTTPException
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.task import Task, TaskStatus, is_valid_transition
from app.models.user import UserRole
from app.repositories.task_repo import TaskRepository
from app.repositories.project_repo import ProjectRepository
from app.repositories.user_repo import UserRepository
from app.schemas.task_schema import TaskCreate, TaskUpdate, TaskStatusUpdate, TaskResponse
from app.utils.logger import get_logger

logger = get_logger(__name__)


class TaskService:
    def __init__(self, db: AsyncSession):
        self.repo = TaskRepository(db)
        self.project_repo = ProjectRepository(db)
        self.user_repo = UserRepository(db)

    async def create_task(self, data: TaskCreate, current_user) -> TaskResponse:
        project = await self.project_repo.get_by_id(data.project_id)
        if not project:
            raise HTTPException(status_code=404, detail="Project not found")

        if data.assignee_id:
            assignee = await self.user_repo.get_by_id(data.assignee_id)
            if not assignee:
                raise HTTPException(status_code=404, detail="Assignee not found")

        task = Task(
            title=data.title,
            description=data.description,
            priority=data.priority,
            project_id=data.project_id,
            assignee_id=data.assignee_id,
            due_date=data.due_date,
        )
        task = await self.repo.create(task)
        task = await self.repo.get_by_id(task.id)
        logger.info(f"Created task: {task.title}")
        return TaskResponse.model_validate(task)

    async def get_tasks(
        self,
        project_id: Optional[int] = None,
        status: Optional[TaskStatus] = None,
        priority=None,
        assignee_id: Optional[int] = None,
        current_user=None,
    ) -> List[TaskResponse]:
        # Employees only see their own tasks
        if current_user and current_user.role == UserRole.employee:
            assignee_id = current_user.id

        tasks = await self.repo.get_all(
            project_id=project_id,
            status=status,
            priority=priority,
            assignee_id=assignee_id,
        )
        return [TaskResponse.model_validate(t) for t in tasks]

    async def get_task(self, task_id: int) -> TaskResponse:
        task = await self.repo.get_by_id(task_id)
        if not task:
            raise HTTPException(status_code=404, detail="Task not found")
        return TaskResponse.model_validate(task)

    async def update_task(self, task_id: int, data: TaskUpdate, current_user) -> TaskResponse:
        task = await self.repo.get_by_id(task_id)
        if not task:
            raise HTTPException(status_code=404, detail="Task not found")

        # Employees can only update their assigned tasks
        if current_user.role == UserRole.employee and task.assignee_id != current_user.id:
            raise HTTPException(status_code=403, detail="You can only update your own tasks")

        # Employees cannot reassign tasks
        if current_user.role == UserRole.employee and data.assignee_id is not None:
            raise HTTPException(status_code=403, detail="Employees cannot reassign tasks")

        for field, value in data.model_dump(exclude_none=True).items():
            setattr(task, field, value)
        task = await self.repo.update(task)
        task = await self.repo.get_by_id(task.id)
        return TaskResponse.model_validate(task)

    async def update_task_status(self, task_id: int, data: TaskStatusUpdate, current_user) -> TaskResponse:
        task = await self.repo.get_by_id(task_id)
        if not task:
            raise HTTPException(status_code=404, detail="Task not found")

        # Employees can only update their assigned tasks
        if current_user.role == UserRole.employee and task.assignee_id != current_user.id:
            raise HTTPException(status_code=403, detail="You can only update your own tasks")

        if not is_valid_transition(task.status, data.status):
            raise HTTPException(
                status_code=400,
                detail=f"Invalid status transition: {task.status} → {data.status}",
            )

        task.status = data.status
        task = await self.repo.update(task)
        task = await self.repo.get_by_id(task.id)
        logger.info(f"Task {task_id} status updated to {data.status}")
        return TaskResponse.model_validate(task)

    async def delete_task(self, task_id: int) -> dict:
        task = await self.repo.get_by_id(task_id)
        if not task:
            raise HTTPException(status_code=404, detail="Task not found")
        await self.repo.delete(task)
        return {"message": "Task deleted"}