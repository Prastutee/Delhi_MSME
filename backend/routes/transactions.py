"""
Transactions API Routes
"""
from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from typing import Optional
import sys
import os

# Add parent to path for imports
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from db import get_db, log_event

router = APIRouter(prefix="/api/transactions", tags=["transactions"])


class SaleRequest(BaseModel):
    customer_id: str
    item_id: str
    quantity: int
    is_credit: bool = True  # True = udhaar, False = cash


class PaymentRequest(BaseModel):
    customer_id: str
    amount: float


@router.get("")
async def list_transactions(limit: int = 100):
    """List recent transactions"""
    try:
        db = get_db()
        result = db.table("transactions").select(
            "*, customers(name, phone)"
        ).order("created_at", desc=True).limit(limit).execute()
        
        return {"transactions": result.data or []}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/sale")
async def record_sale(data: SaleRequest):
    """Record a sale (cash or credit)"""
    try:
        db = get_db()
        
        # Get customer
        customer = db.table("customers").select("name").eq("id", data.customer_id).execute()
        if not customer.data:
            raise HTTPException(status_code=404, detail="Customer not found")
        customer_name = customer.data[0]["name"]
        
        # Get item and update inventory
        item = db.table("inventory").select("*").eq("id", data.item_id).execute()
        if not item.data:
            raise HTTPException(status_code=404, detail="Item not found")
        
        item_data = item.data[0]
        if item_data["quantity"] < data.quantity:
            raise HTTPException(status_code=400, detail="Insufficient stock")
        
        # Reduce inventory
        new_qty = item_data["quantity"] - data.quantity
        db.table("inventory").update({"quantity": new_qty}).eq("id", data.item_id).execute()
        
        # Calculate amount
        amount = item_data["price"] * data.quantity
        tx_type = "sale_credit" if data.is_credit else "sale_paid"
        
        # Record transaction
        tx = db.table("transactions").insert({
            "customer_id": data.customer_id,
            "amount": amount,
            "type": tx_type,
            "description": f"{item_data['item_name']} x{data.quantity} {'(credit)' if data.is_credit else '(cash)'}"
        }).execute()
        
        log_event("web_action", f"Sale: {customer_name} - {item_data['item_name']} x{data.quantity} ₹{amount}", channel="dashboard")
        
        return {
            "success": True,
            "transaction": tx.data[0] if tx.data else None,
            "message": f"Recorded ₹{amount} {tx_type} for {customer_name}"
        }
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/payment")
async def record_payment(data: PaymentRequest):
    """Record a payment from customer"""
    try:
        db = get_db()
        
        # Get customer
        customer = db.table("customers").select("name").eq("id", data.customer_id).execute()
        if not customer.data:
            raise HTTPException(status_code=404, detail="Customer not found")
        customer_name = customer.data[0]["name"]
        
        # Record payment transaction
        tx = db.table("transactions").insert({
            "customer_id": data.customer_id,
            "amount": data.amount,
            "type": "payment",
            "description": f"Payment received: ₹{data.amount}"
        }).execute()
        
        log_event("web_action", f"Payment: {customer_name} paid ₹{data.amount}", channel="dashboard")
        
        return {
            "success": True,
            "transaction": tx.data[0] if tx.data else None,
            "message": f"Recorded ₹{data.amount} payment from {customer_name}"
        }
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
