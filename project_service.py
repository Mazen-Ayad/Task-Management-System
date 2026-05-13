from typing import List
from fastapi import HTTPException
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.project import Project
from app.repositories.project_repo import ProjectRepository
from app.schemas.project_schema import ProjectCreate, ProjectUpdate, ProjectResponse
from app.utils.logger import get_logger

logger = get_logger(__name__)


class ProjectService:
    def __init__(self, db: AsyncSession):
        self.repo = ProjectRepository(db)

    async def create_project(self, data: ProjectCreate, owner_id: int) -> ProjectResponse:
        project = Project(
            name=data.name,
            description=data.description,
            owner_id=owner_id,
        )
        project = await self.repo.create(project)
        logger.info(f"Created project: {project.name}")
        task_count = await self.repo.get_task_count(project.id)
        resp = ProjectResponse.model_validate(project)
        resp.task_count = task_count
        return resp

    async def get_all_projects(self) -> List[ProjectResponse]:
        projects = await self.repo.get_all()
        result = []
        for p in projects:
            tc = await self.repo.get_task_count(p.id)
            r = ProjectResponse.model_validate(p)
            r.task_count = tc
            result.append(r)
        return result

    async def get_project(self, project_id: int) -> ProjectResponse:
        project = await self.repo.get_by_id(project_id)
        if not project:
            raise HTTPException(status_code=404, detail="Project not found")
        tc = await self.repo.get_task_count(project.id)
        r = ProjectResponse.model_validate(project)
        r.task_count = tc
        return r

    async def update_project(self, project_id: int, data: ProjectUpdate, current_user) -> ProjectResponse:
        project = await self.repo.get_by_id(project_id)
        if not project:
            raise HTTPException(status_code=404, detail="Project not found")
        for field, value in data.model_dump(exclude_none=True).items():
            setattr(project, field, value)
        project = await self.repo.update(project)
        tc = await self.repo.get_task_count(project.id)
        r = ProjectResponse.model_validate(project)
        r.task_count = tc
        return r

    async def delete_project(self, project_id: int) -> dict:
        project = await self.repo.get_by_id(project_id)
        if not project:
            raise HTTPException(status_code=404, detail="Project not found")
        await self.repo.delete(project)
        logger.info(f"Deleted project id={project_id}")
        return {"message": "Project deleted"}