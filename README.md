# Blockhouse OA
This is a FastAPI server for managing orders with real-time order status updates via WebSocket. The project is built with SQLModel and PostgreSQL (SQLite for testing). It is containerized with Docker and ready for further deployment enhancements.

## Base URL

- **Local Development:** `http://localhost:80`
- **Production:** `http://your-ec2-ip:80`

---

## Features

- **REST API Endpoints**
  - `POST /orders`: Create a new order.
  - `GET /orders`: Retrieve a list of orders.
- **WebSocket Endpoint**
  - `/ws/orders`: Receive real-time order status updates.
- **Testing**
  - Tests are located under the `tests/` folder using pytest.
- **Containerization**
  - Dockerized application for consistent deployment.
- **DevOps**
  - CI/CD with GitHub Actions in progress.

## Environment Setup

1. Install dependencies:
    ```bash
    pip install -r requirements.txt
    ```

## Running the Application
### Locally
1. Ensure that you have PostgreSQL installed and running.
2. Run the server:
    ```bash
    uvicorn app.main:app --reload
    ```

### Docker
1. Build the Docker image:
    ```bash
    docker build --platform=linux/amd64 -t blockhouse-app .
    ```
2. Run the application container (with .env file):
    ```bash
    docker run --env-file .env -p 80:80 blockhouse-app
    ```
3. Optionally, run the PostgreSQL container:
    ```bash
    docker run --name blockhouse-db -e POSTGRES_PASSWORD=${} -d postgres
    ```

## Testing
Tests are located under the `tests/` folder. Run the tests with the following command:
```bash
pytest tests
```

## Endpoints

### 1. Create Order

- **URL:** `/orders`
- **Method:** `POST`
- **Description:** Create a new order. When an order is created, a background task notifies all connected WebSocket clients about the new order.
- **Headers:** `Content-Type: application/json`
- **Request Body Example:**

  ```json
  {
      "symbol": "dress",
      "price": 500.0,
      "quantity": 5,
      "orderType": "online"
  }
  ```
- **Success Response:** 
    - **Code:** 201 Created
    - **Content:** JSON representation of the created order. For example:

    ```json
    {
        "id": 1,
        "symbol": "dress",
        "price": 500.0,
        "quantity": 5,
        "orderType": "online",
    }
    ```

### 2. Retrieve Orders
- **URL:** `/orders`
- **Method:** `GET`
- **Description:** Retrieve a list of orders.
- **Query Parameters:**
    - `offset` (optional, default: 0): The starting point (index) from which orders are returned.
    - `orderType` (optional, default: 100, maximum: 100): The number of orders to return.
- **Success Response:**
    - **Code:** 200 OK
    - **Content:** A JSON list of order objects. For example:

    ```json
    [
        {
            "id": 1,
            "symbol": "dress",
            "price": 500.0,
            "quantity": 5,
            "orderType": "online",
        },
        {
            "id": 2,
            "symbol": "food",
            "price": 150.0,
            "quantity": 10,
            "orderType": "offline",
        }
    ]
    ```

### 3. WebSocket: Real-Time Order Updates
- **URL:** `/ws/orders`
- **Method:** `WebSocket`
- **Description:** Enables clients to connect via WebSocket to receive real-time updates about order statuses. Notifications are sent when:
1. A new order is created.
2. A client sends an update message.
3. A client disconnects.
- **Client Usage Example (JavaScript):**

    ```javascript
    const ws = new WebSocket('ws://localhost:80/ws/orders');

    ws.onopen = () => {
        console.log('WebSocket connection established.');
    };

    ws.onmessage = (event) => {
        const data = JSON.parse(event.data);
        console.log('Received message:', data);
    };

    ws.onclose = () => {
        console.log('WebSocket connection closed.');
    };
    ```
- **Behavior:**
    - When a client connects, it is added to the connection pool.
    - When a client sends a message, it is broadcasted to all connected clients.
    - On disconnect, a broadcast informs remaining clients that a client has disconnected.

## Database Schema
The database schema consists of a single table, `orders`, with the following columns:
- `id`: The primary key of the order.
- `symbol`: The name of the product.
- `price`: The price of the product.
- `quantity`: The quantity of the product.
- `orderType`: The type of order (online or offline).

## Additional Notes
- **Background Tasks:**
    The `POST /orders` endpoint uses FastAPI's BackgroundTasks to handle broadcasting so that the client receives a quick response without waiting for the broadcast to complete.
- **Database:**
    The API uses SQLModel with PostgreSQL (SQLite for testing). Database connection settings are loaded from environment variables via a `.env` file.

## To-Do
- [x] Server
    - [x] Implement WebSocket support for real-time order status updates

- [ ] DevOps
    - [x] Dockerize the application
    - [ ] Deploy on AWS
        - [x] EC2 for the server
        - [ ] Run PostgreSQL on docker
    - [ ] Implement GitHub actions for CI/CD pipeline
        - [x] Run tests on PRs
        - [ ] Build the container image
        - [ ] SSH into the EC2 instance and deploy the latest version on merge to main
