import pytest
import pytest_asyncio
from httpx import AsyncClient, ASGITransport
from sqlalchemy.ext.asyncio import create_async_engine, async_sessionmaker, AsyncSession

from app.main import app
from app.database.connection import Base
from app.database.session import get_db

TEST_DB_URL = "sqlite+aiosqlite:///./test.db"

test_engine = create_async_engine(TEST_DB_URL, connect_args={"check_same_thread": False})
TestSession = async_sessionmaker(bind=test_engine, class_=AsyncSession, expire_on_commit=False)


async def override_get_db():
    async with TestSession() as session:
        try:
            yield session
            await session.commit()
        except Exception:
            await session.rollback()
            raise


app.dependency_overrides[get_db] = override_get_db


@pytest_asyncio.fixture(scope="session", autouse=True)
async def setup_db():
    async with test_engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    yield
    async with test_engine.begin() as conn:
        await conn.run_sync(Base.metadata.drop_all)
    await test_engine.dispose()


@pytest_asyncio.fixture
async def client():
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as c:
        yield c


@pytest_asyncio.fixture
async def admin_token(client):
    # Create admin directly
    from app.models.user import User, UserRole
    from app.services.auth_service import hash_password
    async with TestSession() as session:
        existing = await session.get(User, 1)
        if not existing:
            admin = User(
                username="testadmin", email="admin@test.com",
                full_name="Test Admin", hashed_password=hash_password("password123"),
                role=UserRole.admin,
            )
            session.add(admin)
            await session.commit()

    resp = await client.post("/api/auth/login", json={"username": "testadmin", "password": "password123"})
    return resp.json()["access_token"]


@pytest_asyncio.fixture
async def employee_token(client, admin_token):
    headers = {"Authorization": f"Bearer {admin_token}"}
    resp = await client.post("/api/users/", json={
        "username": "employee1", "email": "emp@test.com",
        "full_name": "Test Employee", "password": "pass123", "role": "employee"
    }, headers=headers)
    resp2 = await client.post("/api/auth/login", json={"username": "employee1", "password": "pass123"})
    return resp2.json()["access_token"]