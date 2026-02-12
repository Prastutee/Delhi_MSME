from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from datetime import datetime, timedelta
import sys
import os

# Add parent to path for imports
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from db import get_db, log_event

router = APIRouter(prefix="/api/reminders", tags=["Reminders"])

class ReminderRequest(BaseModel):
    customer_id: str
    message: str
    reminder_type: str = "payment"
    repeat_interval_days: int = 7

@router.post("")
async def create_reminder(req: ReminderRequest):
    """Create a new reminder"""
    try:
        db = get_db()
        next_run = datetime.utcnow() + timedelta(days=req.repeat_interval_days)

        result = db.table("reminders").insert({
            "customer_id": req.customer_id,
            "message": req.message,
            "reminder_type": req.reminder_type,
            "repeat_interval_days": req.repeat_interval_days,
            "next_run": next_run.isoformat(),
            "status": "pending"
        }).execute()

        if result.data:
            log_event("web_action", f"Created reminder for customer {req.customer_id}", channel="dashboard")
            return {"status": "ok", "reminder": result.data[0]}
        
        raise HTTPException(status_code=500, detail="Failed to create reminder")
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.get("")
async def list_reminders():
    """List all reminders"""
    try:
        db = get_db()
        # Join with customers to get names
        result = db.table("reminders").select(
            "*, customers(name, phone)"
        ).order("created_at", desc=True).execute()
        return {"reminders": result.data or []}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/{reminder_id}/cancel")
async def cancel_reminder(reminder_id: str):
    """Cancel a reminder"""
    try:
        db = get_db()
        result = db.table("reminders").update({
            "status": "cancelled"
        }).eq("id", reminder_id).execute()

        if not result.data:
            raise HTTPException(status_code=404, detail="Reminder not found")

        log_event("reminder_completed", f"Reminder {reminder_id} cancelled", channel="dashboard")
        return {"status": "cancelled", "reminder": result.data[0]}
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/{reminder_id}/complete")
async def complete_reminder(reminder_id: str):
    """Mark reminder as completed"""
    try:
        db = get_db()
        result = db.table("reminders").update({
            "status": "completed"
        }).eq("id", reminder_id).execute()

        if not result.data:
            raise HTTPException(status_code=404, detail="Reminder not found")

        log_event("reminder_completed", f"Reminder {reminder_id} marked as completed", channel="dashboard")
        return {"status": "completed", "reminder": result.data[0]}
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
