import os
import pytest
from fastapi.testclient import TestClient
from sqlmodel import Session, SQLModel, create_engine
from app.main import app, get_session
import json

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
    data = response.json()
    assert isinstance(data, list)
    assert len(data) == 0


def test_create_order():
    with client.websocket_connect("/ws/orders") as websocket:
        response = client.post(
            "/orders",
            json={"symbol": "food",
                  "price": 150.0,
                  "quantity": 5,
                  "orderType": "online"}
        )

        assert response.status_code == 201
        order = response.json()
        assert order["symbol"] == "food"
        assert order["price"] == 150.0
        assert order["quantity"] == 5
        assert order["orderType"] == "online"

        data = websocket.receive_text()
        assert data == f'{{"message":"New order created: food (Order ID: {order["id"]})"}}'

        response = client.get("/orders")
        orders = response.json()
        assert len(orders) == 1
        assert orders[0]["symbol"] == "food"
        assert orders[0]["price"] == 150.0
        assert orders[0]["quantity"] == 5
        assert orders[0]["orderType"] == "online"


def test_create_order_validation_error():
    # Sending an order with missing required field 'price'
    invalid_payload = {
        "symbol": "MSFT",
        "quantity": 5,
        "orderType": "sell"
    }
    response = client.post("/orders", json=invalid_payload)
    assert response.status_code == 422


def test_websocket_broadcast_and_disconnect():
    with client.websocket_connect("/ws/orders") as ws1:
        with client.websocket_connect("/ws/orders") as ws2:
            # Send a message from ws1 and check that both receive it.
            test_message = "Test websocket broadcast"
            ws1.send_text(test_message)
            received1 = ws1.receive_text()
            received2 = ws2.receive_text()
            try:
                data1 = json.loads(received1)
                data2 = json.loads(received2)
            except Exception as e:
                pytest.fail(f"WebSocket response is not valid JSON: {e}")
            assert test_message in data1.get("message", "")
            assert test_message in data2.get("message", "")

            # Now disconnect ws2 and check that ws1 gets a disconnect notice.
            ws2.close()
            # ws1 should eventually receive broadcast for disconnection.
            disconnect_notice = ws1.receive_text()
            try:
                disconnect_json = json.loads(disconnect_notice)
            except Exception as e:
                pytest.fail(f"WebSocket disconnect response is not valid JSON: {e}")
            assert "A client disconnected" in disconnect_json.get("message", "")


def test_websocket_broadcast():
    with client.websocket_connect("/ws/orders") as websocket:
        websocket.send_text("All Sold Out!")
        data = websocket.receive_text()
        assert data == f'{"message": "Order status update: All Sold Out!"}'


def test_error_handling():
    response = client.post(
        "/orders",
        json={"symbol": "drink",
              "price": "100.0",
              "quantity": 10,
              "orderType": "online"}
    )
    assert response.status_code == 500
    assert response.json() == {"detail": "An error occurred while creating the order."}

    response = client.get("/orders")
    assert response.status_code == 500
    assert response.json() == {"detail": "An error occurred while fetching orders."}


def test_query_params():
    response = client.get("/orders?offset=1&limit=1")
    assert response.status_code == 200
    assert response.json() == [{"symbol": "drink", "price": 100.0, "quantity": 10, "orderType": "online"}]

    response = client.get("/orders?limit=1")