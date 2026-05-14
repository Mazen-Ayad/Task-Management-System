import pytest


@pytest.fixture
async def project_id(client, admin_token):
    resp = await client.post("/api/projects/", json={"name": "Test Project"},
                             headers={"Authorization": f"Bearer {admin_token}"})
    return resp.json()["id"]


@pytest.mark.asyncio
async def test_create_task(client, admin_token, project_id):
    resp = await client.post("/api/tasks/", json={
        "title": "Task 1", "priority": "high", "project_id": project_id
    }, headers={"Authorization": f"Bearer {admin_token}"})
    assert resp.status_code == 200
    assert resp.json()["title"] == "Task 1"
    assert resp.json()["status"] == "todo"


@pytest.mark.asyncio
async def test_task_status_valid_transition(client, admin_token, project_id):
    create = await client.post("/api/tasks/", json={"title": "T2", "project_id": project_id},
                               headers={"Authorization": f"Bearer {admin_token}"})
    tid = create.json()["id"]

    resp = await client.patch(f"/api/tasks/{tid}/status", json={"status": "in_progress"},
                              headers={"Authorization": f"Bearer {admin_token}"})
    assert resp.status_code == 200
    assert resp.json()["status"] == "in_progress"

    resp2 = await client.patch(f"/api/tasks/{tid}/status", json={"status": "done"},
                               headers={"Authorization": f"Bearer {admin_token}"})
    assert resp2.status_code == 200
    assert resp2.json()["status"] == "done"


@pytest.mark.asyncio
async def test_task_status_invalid_transition(client, admin_token, project_id):
    create = await client.post("/api/tasks/", json={"title": "T3", "project_id": project_id},
                               headers={"Authorization": f"Bearer {admin_token}"})
    tid = create.json()["id"]
    # todo -> done is NOT allowed
    resp = await client.patch(f"/api/tasks/{tid}/status", json={"status": "done"},
                              headers={"Authorization": f"Bearer {admin_token}"})
    assert resp.status_code == 400


@pytest.mark.asyncio
async def test_task_filter_by_status(client, admin_token, project_id):
    await client.post("/api/tasks/", json={"title": "FilterTask", "project_id": project_id},
                      headers={"Authorization": f"Bearer {admin_token}"})
    resp = await client.get("/api/tasks/?status=todo", headers={"Authorization": f"Bearer {admin_token}"})
    assert resp.status_code == 200
    for t in resp.json():
        assert t["status"] == "todo"


@pytest.mark.asyncio
async def test_employee_cannot_create_task(client, employee_token, project_id):
    resp = await client.post("/api/tasks/", json={"title": "Nope", "project_id": project_id},
                             headers={"Authorization": f"Bearer {employee_token}"})
    assert resp.status_code == 403


@pytest.mark.asyncio
async def test_done_task_cannot_transition(client, admin_token, project_id):
    create = await client.post("/api/tasks/", json={"title": "FinalTask", "project_id": project_id},
                               headers={"Authorization": f"Bearer {admin_token}"})
    tid = create.json()["id"]
    await client.patch(f"/api/tasks/{tid}/status", json={"status": "in_progress"},
                       headers={"Authorization": f"Bearer {admin_token}"})
    await client.patch(f"/api/tasks/{tid}/status", json={"status": "done"},
                       headers={"Authorization": f"Bearer {admin_token}"})
    # Try to go back to in_progress from done
    resp = await client.patch(f"/api/tasks/{tid}/status", json={"status": "in_progress"},
                              headers={"Authorization": f"Bearer {admin_token}"})
    assert resp.status_code == 400