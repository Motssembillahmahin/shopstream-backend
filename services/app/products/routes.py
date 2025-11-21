from fastapi import APIRouter, HTTPException
import boto3
import time
import uuid
import logging
from decimal import Decimal
from botocore.exceptions import ClientError

from services.app.products.const import TABLE, REGION
from services.app.products.schemas import EventCreate, CreateOrderRequest
from services.app.products.services import create_order_transaction

# Set up logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


dynamodb_resource = boto3.resource("dynamodb", region_name=REGION)
table = dynamodb_resource.Table(TABLE)

router = APIRouter()


@router.post("/events", status_code=201)
def create_event(evt: EventCreate):
    """Create a user event (view, click, etc.)"""
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

    try:
        logger.info(f"Creating event: {item}")
        response = table.put_item(Item=item)
        logger.info(f"Event created successfully. Response: {response}")

        # Verify it was saved
        verify = table.get_item(Key={"PK": item["PK"], "SK": item["SK"]})
        if "Item" in verify:
            logger.info("✓ Verified event exists in database")
        else:
            logger.warning("✗ Event not found after creation!")

        return {"event_id": event_id, "status": "created"}

    except ClientError as e:
        logger.error(f"Error creating event: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/products", status_code=201)
def create_product(product_id: str, name: str, price: float, inventory: int):
    """Create a product (needed before creating orders)"""

    item = {
        "PK": f"PRODUCT#{product_id}",
        "SK": "METADATA",
        "EntityType": "Product",
        "Name": name,
        "Price": Decimal(str(price)),
        "Inventory": inventory,
        "CreatedAt": int(time.time()),
    }

    try:
        logger.info(f"Creating product: {item}")
        table.put_item(Item=item)
        logger.info(f"✓ Product created: {product_id}")
        return {"product_id": product_id, "status": "created"}

    except ClientError as e:
        logger.error(f"Error creating product: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/orders", status_code=201)
def create_order(body: CreateOrderRequest):
    order_id = str(uuid.uuid4())

    total_amount = sum(item.price * item.qty for item in body.items)

    result = create_order_transaction(
        order_id=order_id,
        user_id=body.user_id,
        items=[
            {"product_id": i.product_id, "qty": i.qty, "price": i.price}
            for i in body.items
        ],
        total_amount=total_amount,
    )

    if not result["success"]:
        raise HTTPException(status_code=400, detail=result["error"])

    return {
        "order_id": order_id,
        "status": "created",
        "total": f"{float(total_amount)} BDT",
    }


@router.get("/debug/items")
def debug_list_items():
    """Debug endpoint to see all items in table"""
    try:
        response = table.scan(Limit=50)
        return {"count": response["Count"], "items": response["Items"]}
    except ClientError as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/debug/product/{product_id}")
def debug_get_product(product_id: str):
    """Check if a product exists"""
    try:
        response = table.get_item(Key={"PK": f"PRODUCT#{product_id}", "SK": "METADATA"})
        if "Item" in response:
            return {"exists": True, "product": response["Item"]}
        else:
            return {"exists": False}
    except ClientError as e:
        raise HTTPException(status_code=500, detail=str(e))
