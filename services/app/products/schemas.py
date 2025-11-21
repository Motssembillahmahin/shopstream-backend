from decimal import Decimal

from pydantic import BaseModel


class EventCreate(BaseModel):
    user_id: str
    product_id: str
    shop_id: str
    event_type: str
    payload: dict | None = None


class OrderItem(BaseModel):
    product_id: str
    qty: int
    price: Decimal


class CreateOrderRequest(BaseModel):
    user_id: str
    items: list[OrderItem]
