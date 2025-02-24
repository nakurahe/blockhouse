from sqlmodel import Field, SQLModel


class Order(SQLModel, table=True):
    id: int | None = Field(default=None, primary_key=True)
    symbol: str | None = Field(default=None, index=True)
    price: float
    quantity: int
    orderType: str | None = Field(default=None, index=True)