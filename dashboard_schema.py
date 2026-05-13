from pydantic import BaseModel


class TaskStats(BaseModel):
    total: int
    todo: int
    in_progress: int
    done: int


class DashboardResponse(BaseModel):
    total_users: int
    total_projects: int
    total_tasks: int
    task_stats: TaskStats
    my_tasks: TaskStats