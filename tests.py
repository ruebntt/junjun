from fastapi.testclient import TestClient
from main import app
from dependencies import get_db, create_user
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from models import Base, User, Task

SQLALCHEMY_DATABASE_URL = "sqlite:///./test.db"  
engine = create_engine(SQLALCHEMY_DATABASE_URL, connect_args={"check_same_thread": False})
TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

Base.metadata.create_all(bind=engine)

client = TestClient(app)

def override_get_db():
    try:
        db = TestingSessionLocal()
        yield db
    finally:
        db.close()

app.dependency_overrides[get_db] = override_get_db

def test_create_user():
    response = client.post(
        "/register",
        json={"username": "testuser", "password": "testpass"}
    )
    assert response.status_code == 200
    data = response.json()
    assert data["username"] == "testuser"
    assert "id" in data

def test_login_and_create_task():
    create_user(next(override_get_db()), UserCreate(username="testuser2", password="pass123"))

    response = client.post(
        "/token",
        data={"username": "testuser2", "password": "pass123"}
    )
    assert response.status_code == 200
    token = response.json()["access_token"]
    headers = {"Authorization": f"Bearer {token}"}

    response = client.post(
        "/tasks/",
        headers=headers,
        json={"title": "Test Task", "description": "Test description"}
    )
    assert response.status_code == 200
    task_data = response.json()
    assert task_data["title"] == "Test Task"

    response = client.get("/tasks/", headers=headers)
    assert response.status_code == 200
    tasks = response.json()
    assert any(task["title"] == "Test Task" for task in tasks)

    task_id = task_data["id"]
    response = client.put(
        f"/tasks/{task_id}",
        headers=headers,
        json={"title": "Updated Task"}
    )
    assert response.status_code == 200
    assert response.json()["title"] == "Updated Task"

    # Удаляем задачу
    response = client.delete(f"/tasks/{task_id}", headers=headers)
    assert response.status_code == 204
