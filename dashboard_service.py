from sqlalchemy.ext.asyncio import AsyncSession

from app.repositories.user_repo import UserRepository
from app.repositories.project_repo import ProjectRepository
from app.repositories.task_repo import TaskRepository
from app.models.task import TaskStatus
from app.schemas.dashboard_schema import DashboardResponse, TaskStats


class DashboardService:
    def __init__(self, db: AsyncSession):
        self.user_repo = UserRepository(db)
        self.project_repo = ProjectRepository(db)
        self.task_repo = TaskRepository(db)

    async def get_dashboard(self, current_user) -> DashboardResponse:
        total_users = await self.user_repo.count()
        total_projects = await self.project_repo.count()
        total_tasks = await self.task_repo.count()

        all_stats = await self.task_repo.count_by_status()
        my_stats = await self.task_repo.count_by_status(assignee_id=current_user.id)

        def build_stats(stats_dict) -> TaskStats:
            return TaskStats(
                total=sum(stats_dict.values()),
                todo=stats_dict.get(TaskStatus.todo, 0),
                in_progress=stats_dict.get(TaskStatus.in_progress, 0),
                done=stats_dict.get(TaskStatus.done, 0),
            )

        return DashboardResponse(
            total_users=total_users,
            total_projects=total_projects,
            total_tasks=total_tasks,
            task_stats=build_stats(all_stats),
            my_tasks=build_stats(my_stats),
        )