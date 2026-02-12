"""
Inventory API Routes
"""
from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from typing import Optional
import sys
import os

# Add parent to path for imports
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from db import get_db, log_event, update_inventory

router = APIRouter(prefix="/api/inventory", tags=["inventory"])


class InventoryCreate(BaseModel):
    item_name: str
    quantity: int
    unit: str = "pcs"
    price: float = 0
    low_stock_threshold: int = 10


class InventoryUpdate(BaseModel):
    quantity_change: int  # +ve to add, -ve to reduce
    price: Optional[float] = None


@router.get("")
async def list_inventory():
    """List all inventory items"""
    try:
        db = get_db()
        result = db.table("inventory").select("*").order("item_name").execute()
        items = result.data or []
        
        # Mark low stock items
        for item in items:
            threshold = item.get("low_stock_threshold", 10)
            item["is_low_stock"] = item["quantity"] <= threshold
        
        return {"items": items}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/add")
async def add_inventory_item(data: InventoryCreate):
    """Add new inventory item"""
    try:
        # Use centralized logic from db.py
        result = await update_inventory(
            item_name=data.item_name,
            quantity_change=data.quantity,
            operation="add" if data.quantity > 0 else "set"
        )
        
        # If new item, update extra fields
        if result.get("item_id"):
             db = get_db()
             db.table("inventory").update({
                 "unit": data.unit,
                 "price": data.price,
                 "low_stock_threshold": data.low_stock_threshold
             }).eq("id", result["item_id"]).execute()
             
             # Fetch final to return
             final = db.table("inventory").select("*").eq("id", result["item_id"]).single().execute()
             return {"success": True, "item": final.data}
             
        return {"success": True, "item": result}

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/update/{item_id}")
async def update_inventory_endpoint(item_id: str, data: InventoryUpdate):
    """Update inventory quantity"""
    try:
        # Use centralized logic
        # 1. Update quantity
        
        # Correction: The helper expects NAME. We have ID.
        db = get_db()
        current = db.table("inventory").select("item_name").eq("id", item_id).single().execute()
        if not current.data:
             raise HTTPException(status_code=404, detail="Item not found")
        
        real_name = current.data["item_name"]
        
        # Now call helper
        result = await update_inventory(
            item_name=real_name,
            quantity_change=data.quantity_change,
            operation="add", 
            user_phone="dashboard"
        )
        
        # 2. Update price if needed (Helper doesn't update price)
        if data.price is not None:
             db.table("inventory").update({"price": data.price}).eq("id", item_id).execute()
        
        return {"success": True, "item": result}

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
