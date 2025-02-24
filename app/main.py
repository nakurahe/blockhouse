from typing import Annotated
from fastapi import Depends, FastAPI, Query
from sqlmodel import select
from app.models import Order
from app.database import create_db_and_tables, get_session
from sqlmodel import Session

SessionDep = Annotated[Session, Depends(get_session)]
app = FastAPI()


@app.on_event("startup")
def on_startup():
    create_db_and_tables()


@app.post("/orders")
def create_order(order: Order, session: SessionDep) -> Order:
    session.add(order)
    session.commit()
    session.refresh(order)
    return order


@app.get("/orders")
def read_orders(
    session: SessionDep,
    offset: int = 0,
    limit: Annotated[int, Query(le=100)] = 100
) -> list[Order]:
    orders = session.exec(select(Order).offset(offset).limit(limit)).all()
    return orders
