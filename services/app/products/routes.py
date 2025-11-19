from fastapi import APIRouter
import os
import boto3
import time
import uuid

from services.app.products.schemas import EventCreate

TABLE = os.environ.get("TABLE_NAME", "ShopStreamMain")
dynamodb = boto3.resource("dynamodb")
table = dynamodb.Table(TABLE)

router = APIRouter()


@router.post("/events", status_code=201)
def create_event(evt: EventCreate):
    ts = int(time.time())
    event_id = str(uuid.uuid4())
    item = {
        "PK": f"USER#{evt.user_id}",
        "SK": f"EVENT#{ts}#{event_id}",
        "EntityType": "UserEvent",
        "EventType": evt.event_type,
        "ProductId": f"PRODUCT#{evt.product_id}",
        "ShopId": f"SHOP#{evt.shop_id}",
        "TS": ts,
        "Payload": evt.payload or {},
    }
    table.put_item(Item=item)
    return {"event_id": event_id}
