# Blockhouse OA
This is a FastAPI server for managing orders with real-time order status updates via WebSocket. The project is built with SQLModel and PostgreSQL (SQLite for testing). It is containerized with Docker and ready for further deployment enhancements.

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
