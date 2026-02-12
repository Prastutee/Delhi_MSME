"""
Inventory Management Tool
Update stock via WhatsApp/Telegram with real-time dashboard sync
"""
from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from typing import Optional, List, Dict
from datetime import datetime

router = APIRouter()

# ============================================
# MODELS
# ============================================

class InventoryItem(BaseModel):
    item_name: str
    quantity: int
    unit: str = "pcs"
    price: float = 0
    low_stock_threshold: int = 10


class InventoryUpdate(BaseModel):
    item_name: str
    quantity: int
    operation: str = "set"  # set, add, subtract


class StockAlert(BaseModel):
    item_id: str
    item_name: str
    current_quantity: int
    threshold: int
    alert_type: str  # low_stock, out_of_stock


# ============================================
# INVENTORY OPERATIONS
# ============================================

async def update_stock(
    item_name: str,
    quantity: int,
    operation: str = "subtract",
    user_phone: Optional[str] = None
) -> Dict:
    """
    Update inventory stock
    
    Operations:
    - 'add': Add quantity (stock in)
    - 'subtract': Subtract quantity (stock out / sale)
    - 'set': Set to exact value
    
    Returns updated item info with previous and new values
    """
    from db import update_inventory, check_low_stock
    
    # Use centralized logic
    result = await update_inventory(
        item_name=item_name,
        quantity_change=quantity,
        operation=operation,
        user_phone=user_phone
    )
    
    if not result.get("success"):
         return {"success": False, "message": result.get("error", "Update failed")}
         
    # Format response for the user
    item_display = result["item_name"]
    prev_qty = result["previous"]
    new_qty = result["new"]
    
    action_verb = {
        "add": "added",
        "subtract": "removed",
        "set": "set to"
    }.get(operation, "updated")
    
    message = f"✅ Stock updated: {item_display} {action_verb} {quantity} (Now: {new_qty})"
    
    # Check for low stock alert
    alert = await check_low_stock(item_display)
    if alert:
        message += f"\n\n⚠️ Low Stock Warning: Only {alert['quantity']} left!"
        
    return {
        "success": True,
        "message": message,
        "item": result
    }


async def get_stock(item_name: str) -> Optional[Dict]:
    """Get current stock for an item"""
    from db import get_db
    
    db = get_db()
    result = db.table("inventory")\
        .select("*")\
        .ilike("item_name", f"%{item_name}%")\
        .execute()
    
    if result.data:
        item = result.data[0]
        threshold = item.get("low_stock_threshold", 10)
        return {
            "id": item["id"],
            "name": item["item_name"],
            "quantity": item["quantity"],
            "unit": item.get("unit", "pcs"),
            "price": item.get("price", 0),
            "status": "out_of_stock" if item["quantity"] == 0 
                     else "low_stock" if item["quantity"] <= threshold 
                     else "in_stock",
            "last_updated": item.get("updated_at")
        }
    return None


async def get_low_stock_items() -> List[Dict]:
    """Get all items that are low on stock"""
    from db import get_db
    
    db = get_db()
    
    # Get all items
    result = db.table("inventory").select("*").execute()
    
    low_stock = []
    for item in result.data or []:
        threshold = item.get("low_stock_threshold", 10)
        if item["quantity"] <= threshold:
            low_stock.append({
                "id": item["id"],
                "name": item["item_name"],
                "quantity": item["quantity"],
                "threshold": threshold,
                "unit": item.get("unit", "pcs"),
                "status": "out_of_stock" if item["quantity"] == 0 else "low_stock"
            })
    
    return sorted(low_stock, key=lambda x: x["quantity"])


# ============================================
# API ENDPOINTS (for Dashboard sync)
# ============================================

@router.get("/")
async def list_all_inventory():
    """Get all inventory items - Dashboard will poll this"""
    from db import get_db
    
    db = get_db()
    result = db.table("inventory").select("*").order("item_name").execute()
    
    items = []
    for item in result.data or []:
        threshold = item.get("low_stock_threshold", 10)
        items.append({
            **item,
            "status": "out_of_stock" if item["quantity"] == 0 
                     else "low_stock" if item["quantity"] <= threshold 
                     else "in_stock",
            "value": item["quantity"] * item.get("price", 0)
        })
    
    return {
        "items": items,
        "total_items": len(items),
        "total_value": sum(i["value"] for i in items),
        "last_updated": datetime.now().isoformat()
    }


@router.get("/low_stock")
async def get_low_stock():
    """Get items that need restocking"""
    items = await get_low_stock_items()
    return {
        "low_stock_items": items,
        "count": len(items)
    }


@router.get("/search/{query}")
async def search_inventory(query: str):
    """Search inventory by item name"""
    from db import get_db
    
    db = get_db()
    result = db.table("inventory")\
        .select("*")\
        .ilike("item_name", f"%{query}%")\
        .execute()
    
    return {"results": result.data or [], "query": query}


@router.get("/{item_id}")
async def get_item(item_id: str):
    """Get specific inventory item"""
    from db import get_db
    
    db = get_db()
    result = db.table("inventory").select("*").eq("id", item_id).single().execute()
    
    if not result.data:
        raise HTTPException(status_code=404, detail="Item not found")
    
    return {"item": result.data}


@router.post("/")
async def create_item(item: InventoryItem):
    """Add new inventory item"""
    from db import get_db, log_event
    
    db = get_db()
    
    result = db.table("inventory").insert({
        "item_name": item.item_name,
        "quantity": item.quantity,
        "unit": item.unit,
        "price": item.price,
        "low_stock_threshold": item.low_stock_threshold
    }).execute()
    
    log_event("inventory", f"New item created: {item.item_name}")
    
    return {"item": result.data[0] if result.data else None}


@router.patch("/{item_id}")
async def update_item(item_id: str, update: InventoryUpdate):
    """Update inventory item quantity"""
    from db import get_db, log_event
    
    db = get_db()
    
    # Get current item
    current = db.table("inventory").select("*").eq("id", item_id).single().execute()
    if not current.data:
        raise HTTPException(status_code=404, detail="Item not found")
    
    item = current.data
    previous = item["quantity"]
    
    # Calculate new quantity
    if update.operation == "add":
        new_qty = previous + update.quantity
    elif update.operation == "subtract":
        new_qty = max(0, previous - update.quantity)
    else:
        new_qty = update.quantity
    
    # Update
    db.table("inventory").update({
        "quantity": new_qty,
        "updated_at": datetime.now().isoformat()
    }).eq("id", item_id).execute()
    
    log_event("inventory", f"{item['item_name']}: {previous} → {new_qty}")
    
    return {
        "item_name": item["item_name"],
        "previous": previous,
        "new": new_qty,
        "operation": update.operation
    }


@router.delete("/{item_id}")
async def delete_item(item_id: str):
    """Delete inventory item"""
    from db import get_db, log_event
    
    db = get_db()
    
    # Get item name for logging
    item = db.table("inventory").select("item_name").eq("id", item_id).single().execute()
    
    if not item.data:
        raise HTTPException(status_code=404, detail="Item not found")
    
    db.table("inventory").delete().eq("id", item_id).execute()
    
    log_event("inventory", f"Item deleted: {item.data['item_name']}")
    
    return {"deleted": item.data["item_name"]}


# ============================================
# BULK OPERATIONS
# ============================================

@router.post("/bulk_update")
async def bulk_update(items: List[InventoryUpdate]):
    """Update multiple items at once"""
    results = []
    
    for update in items:
        result = await update_stock(
            item_name=update.item_name,
            quantity=update.quantity,
            operation=update.operation
        )
        results.append(result)
    
    return {
        "updated": len([r for r in results if r.get("success")]),
        "failed": len([r for r in results if not r.get("success")]),
        "results": results
    }


@router.get("/report")
async def inventory_report():
    """Generate inventory report for dashboard"""
    from db import get_db
    
    db = get_db()
    result = db.table("inventory").select("*").execute()
    items = result.data or []
    
    total_items = len(items)
    total_value = sum(i["quantity"] * i.get("price", 0) for i in items)
    out_of_stock = sum(1 for i in items if i["quantity"] == 0)
    low_stock = sum(1 for i in items if 0 < i["quantity"] <= i.get("low_stock_threshold", 10))
    
    return {
        "report_date": datetime.now().isoformat(),
        "summary": {
            "total_items": total_items,
            "total_value": total_value,
            "out_of_stock": out_of_stock,
            "low_stock": low_stock,
            "healthy_stock": total_items - out_of_stock - low_stock
        },
        "top_value_items": sorted(
            items, 
            key=lambda x: x["quantity"] * x.get("price", 0),
            reverse=True
        )[:10],
        "needs_restock": await get_low_stock_items()
    }


# ============================================
# AGENT INTEGRATION HELPERS
# ============================================

async def process_inventory_command(
    item_name: str,
    quantity: int,
    action: str,  # "add", "minus", "set", "check"
    user_phone: Optional[str] = None
) -> str:
    """
    Process inventory command from agent
    
    Called when agent detects inventory intent
    Returns formatted response message
    """
    from db import log_event
    
    if action == "check":
        stock = await get_stock(item_name)
        if stock:
            status_emoji = "❌" if stock["status"] == "out_of_stock" else "⚠️" if stock["status"] == "low_stock" else "✅"
            return f"""📦 *{stock['name']}*

Stock: {stock['quantity']} {stock['unit']} {status_emoji}
Price: ₹{stock['price']:.2f}
Value: ₹{stock['quantity'] * stock['price']:,.2f}
Status: {stock['status'].replace('_', ' ').title()}"""
        else:
            return f"❌ '{item_name}' inventory mein nahi mila"
    
    # Map action to operation
    operation = "add" if action in ["add", "plus"] else "subtract" if action in ["minus", "subtract", "remove"] else "set"
    
    result = await update_stock(
        item_name=item_name,
        quantity=quantity,
        operation=operation,
        user_phone=user_phone
    )
    
    if result["success"]:
        item = result["item"]
        alert_msg = f"\n\n{result['alert']['message']}" if result.get("alert") else ""
        
        return f"""📦 *Inventory Updated!*

Item: {item['name']}
Previous: {item['previous_quantity']}
Change: {'+' if operation == 'add' else '-' if operation == 'subtract' else '='}{quantity}
*New Stock: {item['new_quantity']}*{alert_msg}"""
    else:
        return f"❌ {result.get('error', 'Update failed')}"
