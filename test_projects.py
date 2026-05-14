import pytest


@pytest.mark.asyncio
async def test_create_project(client, admin_token):
    resp = await client.post("/api/projects/", json={"name": "Alpha", "description": "First project"},
                             headers={"Authorization": f"Bearer {admin_token}"})
    assert resp.status_code == 200
    assert resp.json()["name"] == "Alpha"


@pytest.mark.asyncio
async def test_list_projects(client, admin_token):
    resp = await client.get("/api/projects/", headers={"Authorization": f"Bearer {admin_token}"})
    assert resp.status_code == 200
    assert isinstance(resp.json(), list)


@pytest.mark.asyncio
async def test_employee_cannot_create_project(client, employee_token):
    resp = await client.post("/api/projects/", json={"name": "Nope"},
                             headers={"Authorization": f"Bearer {employee_token}"})
    assert resp.status_code == 403


@pytest.mark.asyncio
async def test_get_project(client, admin_token):
    create = await client.post("/api/projects/", json={"name": "Beta"},
                               headers={"Authorization": f"Bearer {admin_token}"})
    pid = create.json()["id"]
    resp = await client.get(f"/api/projects/{pid}", headers={"Authorization": f"Bearer {admin_token}"})
    assert resp.status_code == 200
    assert resp.json()["id"] == pid


@pytest.mark.asyncio
async def test_update_project(client, admin_token):
    create = await client.post("/api/projects/", json={"name": "Gamma"},
                               headers={"Authorization": f"Bearer {admin_token}"})
    pid = create.json()["id"]
    resp = await client.patch(f"/api/projects/{pid}", json={"status": "completed"},
                              headers={"Authorization": f"Bearer {admin_token}"})
    assert resp.status_code == 200
    assert resp.json()["status"] == "completed"