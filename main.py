from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse
import os

from app.core.config import settings
from app.database.connection import engine, Base
from app.routes import auth, users, projects, tasks, dashboard
from app.utils.logger import get_logger

logger = get_logger(__name__)

# Import all models so Base knows about them
from app.models import user, project, task  # noqa


async def seed_admin():
    """Create a default admin user if none exists."""
    from app.database.session import AsyncSessionLocal
    from app.repositories.user_repo import UserRepository
    from app.models.user import User, UserRole
    from app.services.auth_service import hash_password

    async with AsyncSessionLocal() as session:
        repo = UserRepository(session)
        existing = await repo.get_by_username("admin")
        if not existing:
            admin = User(
                username="admin",
                email="admin@taskmanager.com",
                full_name="System Administrator",
                hashed_password=hash_password("admin123"),
                role=UserRole.admin,
            )
            session.add(admin)
            await session.commit()
            logger.info("Default admin user created: admin / admin123")


@asynccontextmanager
async def lifespan(app: FastAPI):
    # Startup
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    await seed_admin()
    logger.info(f"{settings.APP_NAME} started")
    yield
    # Shutdown
    await engine.dispose()
    logger.info("Application shutdown")


app = FastAPI(
    title=settings.APP_NAME,
    version="1.0.0",
    description="Backend system for managing projects and tracking tasks",
    lifespan=lifespan,
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# API Routes
app.include_router(auth.router)
app.include_router(users.router)
app.include_router(projects.router)
app.include_router(tasks.router)
app.include_router(dashboard.router)

# Serve frontend
FRONTEND_DIR = os.path.join(os.path.dirname(__file__), "..", "frontend")
if os.path.exists(FRONTEND_DIR):
    app.mount("/static", StaticFiles(directory=os.path.join(FRONTEND_DIR, "css"), html=False), name="css")
    app.mount("/js", StaticFiles(directory=os.path.join(FRONTEND_DIR, "js"), html=False), name="js")

    @app.get("/", include_in_schema=False)
    async def serve_index():
        return FileResponse(os.path.join(FRONTEND_DIR, "login.html"))

    @app.get("/dashboard", include_in_schema=False)
    async def serve_dashboard():
        return FileResponse(os.path.join(FRONTEND_DIR, "dashboard.html"))

    @app.get("/login", include_in_schema=False)
    async def serve_login():
        return FileResponse(os.path.join(FRONTEND_DIR, "login.html"))


@app.get("/health", tags=["Health"])
async def health():
    return {"status": "ok", "app": settings.APP_NAME}