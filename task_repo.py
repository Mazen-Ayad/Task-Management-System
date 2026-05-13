from typing import Optional, List
from sqlalchemy import select, func
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.models.task import Task, TaskStatus, TaskPriority


class TaskRepository:
    def __init__(self, db: AsyncSession):
        self.db = db

    async def get_by_id(self, task_id: int) -> Optional[Task]:
        result = await self.db.execute(
            select(Task).options(selectinload(Task.assignee)).where(Task.id == task_id)
        )
        return result.scalar_one_or_none()

    async def get_all(
        self,
        project_id: Optional[int] = None,
        status: Optional[TaskStatus] = None,
        priority: Optional[TaskPriority] = None,
        assignee_id: Optional[int] = None,
    ) -> List[Task]:
        query = select(Task).options(selectinload(Task.assignee))
        if project_id:
            query = query.where(Task.project_id == project_id)
        if status:
            query = query.where(Task.status == status)
        if priority:
            query = query.where(Task.priority == priority)
        if assignee_id:
            query = query.where(Task.assignee_id == assignee_id)
        result = await self.db.execute(query)
        return list(result.scalars().all())

    async def create(self, task: Task) -> Task:
        self.db.add(task)
        await self.db.flush()
        await self.db.refresh(task)
        return task

    async def update(self, task: Task) -> Task:
        await self.db.flush()
        await self.db.refresh(task)
        return task

    async def delete(self, task: Task) -> None:
        await self.db.delete(task)
        await self.db.flush()

    async def count_by_status(self, assignee_id: Optional[int] = None):
        query = select(Task.status, func.count().label("count")).group_by(Task.status)
        if assignee_id:
            query = query.where(Task.assignee_id == assignee_id)
        result = await self.db.execute(query)
        return {row.status: row.count for row in result.all()}

    async def count(self) -> int:
        result = await self.db.execute(select(func.count()).select_from(Task))
        return result.scalar()