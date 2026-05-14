import pytest


@pytest.mark.asyncio
async def test_create_user(client, admin_token):
    headers = {"Authorization": f"Bearer {admin_token}"}
    resp = await client.post("/api/users/", json={
        "username": "newuser1", "email": "new1@test.com",
        "full_name": "New User", "password": "pass123", "role": "employee"
    }, headers=headers)
    assert resp.status_code == 200
    assert resp.json()["username"] == "newuser1"


@pytest.mark.asyncio
async def test_create_user_duplicate_username(client, admin_token):
    headers = {"Authorization": f"Bearer {admin_token}"}
    await client.post("/api/users/", json={
        "username": "dupuser", "email": "dup1@test.com",
        "full_name": "Dup", "password": "pass", "role": "employee"
    }, headers=headers)
    resp = await client.post("/api/users/", json={
        "username": "dupuser", "email": "dup2@test.com",
        "full_name": "Dup2", "password": "pass", "role": "employee"
    }, headers=headers)
    assert resp.status_code == 400


@pytest.mark.asyncio
async def test_employee_cannot_create_user(client, employee_token):
    resp = await client.post("/api/users/", json={
        "username": "x", "email": "x@x.com", "full_name": "X", "password": "x", "role": "employee"
    }, headers={"Authorization": f"Bearer {employee_token}"})
    assert resp.status_code == 403


@pytest.mark.asyncio
async def test_list_users(client, admin_token):
    resp = await client.get("/api/users/", headers={"Authorization": f"Bearer {admin_token}"})
    assert resp.status_code == 200
    assert isinstance(resp.json(), list)


@pytest.mark.asyncio
async def test_update_user(client, admin_token):
    headers = {"Authorization": f"Bearer {admin_token}"}
    create = await client.post("/api/users/", json={
        "username": "updatable", "email": "upd@test.com",
        "full_name": "Old Name", "password": "pass", "role": "employee"
    }, headers=headers)
    uid = create.json()["id"]
    resp = await client.patch(f"/api/users/{uid}", json={"full_name": "New Name"}, headers=headers)
    assert resp.status_code == 200
    assert resp.json()["full_name"] == "New Name"