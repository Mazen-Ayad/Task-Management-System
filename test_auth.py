import pytest


@pytest.mark.asyncio
async def test_login_success(client, admin_token):
    assert admin_token is not None


@pytest.mark.asyncio
async def test_login_wrong_password(client):
    resp = await client.post("/api/auth/login", json={"username": "testadmin", "password": "wrong"})
    assert resp.status_code == 401


@pytest.mark.asyncio
async def test_login_unknown_user(client):
    resp = await client.post("/api/auth/login", json={"username": "ghost", "password": "x"})
    assert resp.status_code == 401


@pytest.mark.asyncio
async def test_get_me(client, admin_token):
    resp = await client.get("/api/users/me", headers={"Authorization": f"Bearer {admin_token}"})
    assert resp.status_code == 200
    data = resp.json()
    assert data["username"] == "testadmin"
    assert data["role"] == "admin"


@pytest.mark.asyncio
async def test_protected_without_token(client):
    resp = await client.get("/api/users/me")
    assert resp.status_code == 401