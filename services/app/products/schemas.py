from pydantic import BaseModel


class EventCreate(BaseModel):
    user_id: str
    product_id: str
    shop_id: str
    event_type: str
    payload: dict | None = None
