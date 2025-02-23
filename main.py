from typing import Annotated

from fastapi import Depends, FastAPI, Query
from sqlmodel import Field, Session, SQLModel, create_engine, select


class Order(SQLModel, table=True):
    id: int | None = Field(default=None, primary_key=True)
    symbol: str | None = Field(default=None, index=True)
    price: float
    quantity: int
    orderType: str | None = Field(default=None, index=True)


sqlite_file_name = "database.db"
sqlite_url = f"sqlite:///{sqlite_file_name}"

connect_args = {"check_same_thread": False}
engine = create_engine(sqlite_url, connect_args=connect_args)


def create_db_and_tables():
    SQLModel.metadata.create_all(engine)


def get_session():
    with Session(engine) as session:
        yield session


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
    offset=0,
    limit=Annotated[int, Query(le=100)](100)
) -> list[Order]:
    orders = session.exec(select(Order).offset(offset).limit(limit)).all()
    return orders
