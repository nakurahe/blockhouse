import json
import logging
from typing import Annotated

from fastapi import Depends, FastAPI, HTTPException, Query, WebSocket, WebSocketDisconnect, BackgroundTasks, status
from sqlmodel import select, Session
from app.models import Order, ConnectionManager
from app.database import create_db_and_tables, get_session

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

SessionDep = Annotated[Session, Depends(get_session)]
app = FastAPI()


@app.on_event("startup")
def on_startup():
    try:
        create_db_and_tables()
        logger.info("Database created and tables are ready.")
    except Exception as e:
        logger.exception("Error during database initialization: %s", e)
        raise e


@app.post("/orders", response_model=Order, status_code=status.HTTP_201_CREATED)
def create_order(
    order: Order,
    background_tasks: BackgroundTasks,
    session: SessionDep
) -> Order:
    try:
        session.add(order)
        session.commit()
        session.refresh(order)
    except Exception as e:
        logger.exception("Failed to create order: %s", e)
        session.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="An error occurred while creating the order."
        )

    # Broadcast new order creation to all connected WebSocket clients.
    try:
        message = json.dumps({
            "message": f"New order created: {order.symbol} (Order ID: {order.id})"
        })
        background_tasks.add_task(manager.broadcast, message)
    except Exception as e:
        logger.exception("Broadcast failed: %s", e)
    return order


@app.get("/orders", response_model=list[Order])
def read_orders(
    session: SessionDep,
    offset: int = 0,
    limit: Annotated[int, Query(le=100)] = 100
) -> list[Order]:
    try:
        orders = session.exec(select(Order).offset(offset).limit(limit)).all()
        return orders
    except Exception as e:
        logger.exception("Failed to retrieve orders: %s", e)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="An error occurred while fetching orders."
        )


manager = ConnectionManager()


@app.websocket("/ws/orders")
async def websocket_endpoint(websocket: WebSocket):
    await manager.connect(websocket)
    try:
        while True:
            data = await websocket.receive_text()
            try:
                await manager.broadcast(json.dumps({"message": f"Order status update: {data}"}))
            except Exception as e:
                logger.exception("Error broadcasting message over websocket: %s", e)
                await websocket.send_text("An error occurred while broadcasting your message.")
    except WebSocketDisconnect:
        manager.disconnect(websocket)
        try:
            await manager.broadcast(json.dumps({"message": "A client disconnected"}))
        except Exception as e:
            logger.exception("Error broadcasting disconnect message: %s", e)
    except Exception as e:
        logger.exception("Unexpected error in websocket connection: %s", e)
        # Optionally, send an error message to the client:
        await websocket.send_text("An unexpected server error occurred.")
        await websocket.close(code=1001)
