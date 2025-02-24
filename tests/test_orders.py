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
    assert response.json() == []


def test_create_order():
    response = client.post(
        "/orders",
        json={"symbol": "food",
              "price": 150.0,
              "quantity": 5,
              "orderType": "off-line"}
    )

    assert response.status_code == 200
    order = response.json()
    assert order["symbol"] == "food"
    assert order["price"] == 150.0
    assert order["quantity"] == 5
    assert order["orderType"] == "off-line"

    response = client.get("/orders")
    assert response.status_code == 200
    orders = response.json()
    assert len(orders) == 1
    assert orders[0]["symbol"] == "food"
    assert orders[0]["price"] == 150.0
    assert orders[0]["quantity"] == 5
    assert orders[0]["orderType"] == "off-line"


def test_websocket_broadcast():
    with client.websocket_connect("/ws/orders") as websocket:
        websocket.send_text("All Sold Out!")
        data = websocket.receive_text()
        assert data == "Order status update: All Sold Out!"

        response = client.post(
            "/orders",
            json={"symbol": "drink",
                  "price": 100.0,
                  "quantity": 10,
                  "orderType": "online"}
        )
        order = response.json()

        data = websocket.receive_text()
        assert data == f"New order created: drink (Order ID: {order['id']})"

        response = client.get("/orders")
        orders = response.json()
        assert len(orders) == 2
        assert orders[1]["symbol"] == "drink"
        assert orders[1]["price"] == 100.0
        assert orders[1]["quantity"] == 10
        assert orders[1]["orderType"] == "online"
