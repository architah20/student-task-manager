import pytest

from app import create_app


@pytest.fixture()
def client():
    app = create_app(
        {"TESTING": True, "SQLALCHEMY_DATABASE_URI": "sqlite:///:memory:"}
    )
    with app.test_client() as client:
        yield client


def create(client, **overrides):
    payload = {"title": "Finish DevOps lab", "description": "Experiment 1"}
    payload.update(overrides)
    return client.post("/api/tasks", json=payload)


def test_health(client):
    response = client.get("/health")
    assert response.status_code == 200
    assert response.get_json() == {"status": "ok"}


def test_home_page_loads(client):
    response = client.get("/")
    assert response.status_code == 200
    assert b"Student Task Manager" in response.data


def test_create_task(client):
    response = create(client, due_date="2026-12-31")
    assert response.status_code == 201
    body = response.get_json()
    assert body["title"] == "Finish DevOps lab"
    assert body["status"] == "pending"
    assert body["due_date"] == "2026-12-31"


def test_create_task_requires_title(client):
    response = client.post("/api/tasks", json={"description": "no title"})
    assert response.status_code == 400
    assert "title" in response.get_json()["errors"]


def test_create_task_rejects_bad_date(client):
    response = create(client, due_date="31-12-2026")
    assert response.status_code == 400
    assert "due_date" in response.get_json()["errors"]


def test_list_tasks(client):
    create(client, title="Task A")
    create(client, title="Task B")
    response = client.get("/api/tasks")
    assert response.status_code == 200
    assert len(response.get_json()) == 2


def test_get_single_task(client):
    task_id = create(client).get_json()["id"]
    response = client.get(f"/api/tasks/{task_id}")
    assert response.status_code == 200
    assert response.get_json()["id"] == task_id


def test_get_missing_task_returns_404(client):
    response = client.get("/api/tasks/999")
    assert response.status_code == 404


def test_update_task_marks_done(client):
    task_id = create(client).get_json()["id"]
    response = client.put(f"/api/tasks/{task_id}", json={"status": "done"})
    assert response.status_code == 200
    assert response.get_json()["status"] == "done"


def test_update_rejects_invalid_status(client):
    task_id = create(client).get_json()["id"]
    response = client.put(f"/api/tasks/{task_id}", json={"status": "later"})
    assert response.status_code == 400


def test_filter_by_status(client):
    done_id = create(client, title="Done task").get_json()["id"]
    create(client, title="Pending task")
    client.put(f"/api/tasks/{done_id}", json={"status": "done"})
    done = client.get("/api/tasks?status=done").get_json()
    assert [t["title"] for t in done] == ["Done task"]


def test_delete_task(client):
    task_id = create(client).get_json()["id"]
    assert client.delete(f"/api/tasks/{task_id}").status_code == 204
    assert client.get(f"/api/tasks/{task_id}").status_code == 404


def test_metrics_endpoint(client):
    create(client)
    response = client.get("/metrics")
    assert response.status_code == 200
    assert b"tasks_created_total" in response.data
    assert b"tasks_pending" in response.data
