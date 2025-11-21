import logging
from datetime import datetime

import boto3
from botocore.exceptions import ClientError
from decimal import Decimal

from services.app.products.const import REGION, TABLE

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

dynamodb = boto3.client("dynamodb")
dynamodb_client = boto3.client("dynamodb", region_name=REGION)


def create_order_transaction(
    order_id: str, user_id: str, items: list, total_amount: Decimal
):
    """Create order with atomic inventory update"""
    transact_items = []

    # Create order metadata
    order_item = {
        "PK": {"S": f"ORDER#{order_id}"},
        "SK": {"S": "METADATA"},
        "EntityType": {"S": "Order"},
        "UserId": {"S": f"USER#{user_id}"},
        "Status": {"S": "PENDING"},
        "TotalAmount": {"N": str(total_amount)},
        "CreatedAt": {"N": str(int(datetime.now().timestamp()))},
        "ItemCount": {"N": str(len(items))},
    }
    transact_items.append(
        {
            "Put": {
                "TableName": TABLE,
                "Item": order_item,
                "ConditionExpression": "attribute_not_exists(PK)",
            }
        }
    )

    # Create order line items and update inventory
    for idx, it in enumerate(items):
        # Order line item
        order_line_item = {
            "PK": {"S": f"ORDER#{order_id}"},
            "SK": {"S": f"ITEM#{idx:03d}"},
            "EntityType": {"S": "OrderItem"},
            "ProductId": {"S": f"PRODUCT#{it['product_id']}"},
            "Quantity": {"N": str(it["qty"])},
            "Price": {"N": str(it["price"])},
        }
        transact_items.append({"Put": {"TableName": TABLE, "Item": order_line_item}})

        # Update product inventory
        key = {"PK": {"S": f"PRODUCT#{it['product_id']}"}, "SK": {"S": "METADATA"}}
        update = {
            "TableName": TABLE,
            "Key": key,
            "UpdateExpression": "SET Inventory = Inventory - :q",
            "ConditionExpression": "Inventory >= :q AND attribute_exists(PK)",
            "ExpressionAttributeValues": {":q": {"N": str(it["qty"])}},
        }
        transact_items.append({"Update": update})

    try:
        logger.info(f"Creating order transaction with {len(transact_items)} items")
        dynamodb_client.transact_write_items(TransactItems=transact_items)
        logger.info(f"✓ Order {order_id} created successfully")
        return {"success": True, "order_id": order_id}

    except ClientError as e:
        error_code = e.response["Error"]["Code"]
        logger.error(f"Transaction failed: {error_code}")

        if error_code == "TransactionCanceledException":
            reasons = e.response.get("CancellationReasons", [])
            logger.error(f"Cancellation reasons: {reasons}")

            for reason in reasons:
                if reason.get("Code") == "ConditionalCheckFailed":
                    return {
                        "success": False,
                        "error": "Insufficient inventory or product not found",
                    }
        raise
