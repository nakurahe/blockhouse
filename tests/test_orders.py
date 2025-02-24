import os
import pytest
from fastapi.testclient import TestClient
from sqlmodel import Session, SQLModel, create_engine
from app.main import app, get_session

TEST_DB_PATH = os.path.join(os.path.dirname(__file__), "database.db")
DATABASE_URL = f"sqlite:///{TEST_DB_PATH}"


engine_test = create_engine(
    DATABASE_URL, 
    echo=False, 
    connect_args={"check_same_thread": False}
)


def create_test_db():
    if os.path.exists(TEST_DB_PATH):
        os.remove(TEST_DB_PATH)
    SQLModel.metadata.create_all(engine_test)


def override_get_session():
    with Session(engine_test) as session:
        yield session


app.dependency_overrides[get_session] = override_get_session

client = TestClient(app)


@pytest.fixture(autouse=True, scope="module")
def setup_db():
    create_test_db()
    yield


def test_get_orders():
    response = client.get("/orders")
    assert response.status_code == 200
