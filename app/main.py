from typing import Annotated
from fastapi import Depends, FastAPI, Query, WebSocket, WebSocketDisconnect, BackgroundTasks
from sqlmodel import select, Session
from app.models import Order, ConnectionManager
from app.database import create_db_and_tables, get_session


SessionDep = Annotated[Session, Depends(get_session)]
app = FastAPI()

@app.on_event("startup")
def on_startup():
    create_db_and_tables()


@app.post("/orders")
def create_order(
    order: Order,
    background_tasks: BackgroundTasks,
    session: SessionDep
) -> Order:
    session.add(order)
    session.commit()
    session.refresh(order)
    # Broadcast creation of the new order to all connected WebSocket clients.
    background_tasks.add_task(
        manager.broadcast,
        f"New order created: {order.symbol} (Order ID: {order.id})"
    )
    return order


@app.get("/orders")
def read_orders(
    session: SessionDep,
    offset: int = 0,
    limit: Annotated[int, Query(le=100)] = 100
) -> list[Order]:
    orders = session.exec(select(Order).offset(offset).limit(limit)).all()
    return orders


manager = ConnectionManager()


@app.websocket("/ws/orders")
async def websocket_endpoint(websocket: WebSocket):
    await manager.connect(websocket)
    try:
        while True:
            data = await websocket.receive_text()
            await manager.broadcast(f"Order status update: {data}")
    except WebSocketDisconnect:
        manager.disconnect(websocket)
        await manager.broadcast("A client disconnected")
