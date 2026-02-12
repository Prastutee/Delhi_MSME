from fastapi import APIRouter, HTTPException, Depends
from typing import Dict, Any, List
from db import get_db, list_inventory, list_invoices, get_logs
from datetime import datetime

router = APIRouter(prefix="/api/dashboard", tags=["Dashboard"])

@router.get("/metrics")
async def get_dashboard_metrics() -> Dict[str, Any]:
    """
    Get unified dashboard metrics.
    Single source of truth for Overview and Inventory pages.
    """
    try:
        db = get_db()
        
        # 1. Inventory Metrics
        # Fetch all items to ensure consistency with Inventory page
        inventory_items = await list_inventory()
        
        total_item_types = len(inventory_items)
        total_stock_units = sum(item.get("quantity", 0) for item in inventory_items)
        
        # Calculate low stock using same logic as backend alerts
        # Threshold fallback to 10 if not set
        low_stock_items = [
            item for item in inventory_items 
            if item.get("quantity", 0) <= (item.get("low_stock_threshold") or 10)
        ]
        low_stock_count = len(low_stock_items)
        
        # 2. Invoices Metrics
        invoices = await list_invoices()
        
        pending_invoices = [inv for inv in invoices if inv["status"] == "pending"]
        overdue_invoices = [
            inv for inv in invoices 
            if inv["status"] in ["pending", "overdue"] and 
            inv.get("due_date") and 
            inv["due_date"] < datetime.now().strftime("%Y-%m-%d")
        ]
        
        pending_count = len(pending_invoices)
        pending_amount = sum(inv["amount"] for inv in pending_invoices)
        
        overdue_count = len(overdue_invoices)
        overdue_amount = sum(inv["amount"] for inv in overdue_invoices)
        
        # 3. Activity Metrics
        # Count today's logs
        today_str = datetime.now().strftime("%Y-%m-%d")
        # Query DB directly for count to avoid fetching all logs if list is huge
        # But db.get_logs has limit. We'll use a count query or just fetch recent.
        # For now, fetching recent 100 is likely enough for "Today's Actions" 
        # but if activity is high, count might be wrong.
        # Ideally: db.table("logs").select("id", count="exact").gte("created_at", today_str).execute()
        # reusing get_logs for simplicity but it lists limited.
        # Let's do a direct count query here for accuracy.
        today_logs = db.table("logs").select("id", count="exact").gte("created_at", today_str).execute()
        today_activity = today_logs.count if today_logs.count is not None else len(today_logs.data)

        return {
            "total_item_types": total_item_types,
            "total_stock_units": total_stock_units,
            "lowStockCount": low_stock_count,  # Camels for frontend compat
            "pendingCount": pending_count,
            "pendingAmount": pending_amount,
            "overdueCount": overdue_count,
            "overdueAmount": overdue_amount,
            "todayActivity": today_activity
        }

    except Exception as e:
        print(f"Error fetching dashboard metrics: {e}")
        raise HTTPException(status_code=500, detail=str(e))
