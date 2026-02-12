"""
Customers API Routes
"""
from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from typing import Optional
import sys
import os

# Add parent to path for imports
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from db import get_db, log_event

router = APIRouter(prefix="/api/customers", tags=["customers"])


class CustomerCreate(BaseModel):
    name: str
    phone: str


class CustomerUpdate(BaseModel):
    name: Optional[str] = None
    phone: Optional[str] = None


@router.get("")
async def list_customers():
    """List all customers with balances"""
    try:
        db = get_db()
        
        # Get customers
        result = db.table("customers").select("*").order("name").execute()
        customers = result.data or []
        
        # Get transactions for balance calculation
        tx_result = db.table("transactions").select("customer_id, amount, type").execute()
        transactions = tx_result.data or []
        
        # Calculate balances
        balances = {}
        for tx in transactions:
            cid = tx.get("customer_id")
            if not cid:
                continue
            if cid not in balances:
                balances[cid] = 0
            if tx["type"] in ["credit", "sale_credit"]:
                balances[cid] += tx["amount"]
            elif tx["type"] == "payment":
                balances[cid] -= tx["amount"]
        
        # Add balance to customers
        for c in customers:
            c["balance"] = balances.get(c["id"], 0)
        
        return {"customers": customers}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/add")
async def add_customer(data: CustomerCreate):
    """Add a new customer"""
    try:
        db = get_db()
        
        # Check if phone already exists
        existing = db.table("customers").select("id").eq("phone", data.phone).execute()
        if existing.data:
            raise HTTPException(status_code=400, detail="Phone already registered")
        
        result = db.table("customers").insert({
            "name": data.name,
            "phone": data.phone
        }).execute()
        
        if result.data:
            log_event("web_action", f"Added customer: {data.name}", channel="dashboard")
            return {"success": True, "customer": result.data[0]}
        
        raise HTTPException(status_code=500, detail="Failed to add customer")
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.put("/{customer_id}")
async def update_customer(customer_id: str, data: CustomerUpdate):
    """Update customer details"""
    try:
        db = get_db()
        
        update_data = {}
        if data.name:
            update_data["name"] = data.name
        if data.phone:
            update_data["phone"] = data.phone
        
        if not update_data:
            raise HTTPException(status_code=400, detail="No data to update")
        
        result = db.table("customers").update(update_data).eq("id", customer_id).execute()
        
        if result.data:
            log_event("web_action", f"Updated customer: {customer_id}", channel="dashboard")
            return {"success": True, "customer": result.data[0]}
        
        raise HTTPException(status_code=404, detail="Customer not found")
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
