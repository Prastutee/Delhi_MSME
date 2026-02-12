"""
Logging and Audit Trail System
All business actions logged to Supabase for compliance and dashboard display
"""
from fastapi import APIRouter, Query
from typing import Optional, List, Dict
from datetime import datetime, date, timedelta
from enum import Enum

router = APIRouter()


# ============================================
# LOG ACTION TYPES
# ============================================

class ActionType(str, Enum):
    # Invoice actions
    INVOICE_CREATED = "invoice_created"
    INVOICE_SENT = "invoice_sent"
    INVOICE_PAID = "invoice_paid"
    INVOICE_CANCELLED = "invoice_cancelled"
    INVOICE_OVERDUE = "invoice_overdue"
    
    # Payment actions
    PAYMENT_RECEIVED = "payment_received"
    PAYMENT_RECORDED = "payment_recorded"
    
    # Reminder actions
    REMINDER_SENT = "reminder_sent"
    REMINDER_SCHEDULED = "reminder_scheduled"
    
    # Inventory actions
    INVENTORY_UPDATED = "inventory_updated"
    INVENTORY_ADDED = "inventory_added"
    INVENTORY_LOW_STOCK = "inventory_low_stock"
    INVENTORY_OUT_OF_STOCK = "inventory_out_of_stock"
    
    # User actions
    ACTION_CONFIRMED = "action_confirmed"
    ACTION_CANCELLED = "action_cancelled"
    ACTION_EXPIRED = "action_expired"
    
    # System actions
    SYSTEM_START = "system_start"
    SYSTEM_ERROR = "system_error"
    
    # Channel actions
    WHATSAPP_MESSAGE = "whatsapp"
    TELEGRAM_MESSAGE = "telegram"
    
    # OCR/Voice
    OCR_PROCESSED = "ocr"
    VOICE_TRANSCRIBED = "voice"


# Action type icons for display
ACTION_ICONS = {
    "invoice_created": "📄",
    "invoice_sent": "📤",
    "invoice_paid": "✅",
    "invoice_cancelled": "❌",
    "invoice_overdue": "⏰",
    "payment_received": "💰",
    "payment_recorded": "💳",
    "reminder_sent": "🔔",
    "reminder_scheduled": "⏰",
    "inventory_updated": "📦",
    "inventory_added": "➕",
    "inventory_low_stock": "⚠️",
    "inventory_out_of_stock": "🚨",
    "action_confirmed": "✅",
    "action_cancelled": "❌",
    "action_expired": "⏱️",
    "system_start": "🚀",
    "system_error": "❌",
    "whatsapp": "📱",
    "telegram": "✈️",
    "ocr": "📷",
    "voice": "🎤",
    "error": "❌",
    "system": "⚙️",
}


# ============================================
# CORE LOGGING FUNCTIONS
# ============================================

def log_action(
    action_type: str,
    message: str,
    user_phone: Optional[str] = None,
    channel: Optional[str] = None,
    metadata: Optional[Dict] = None
) -> Optional[str]:
    """
    Log an action to the database
    
    Args:
        action_type: Type of action (use ActionType enum values)
        message: Human-readable description
        user_phone: User's phone number (if applicable)
        channel: Communication channel (whatsapp, telegram, dashboard)
        metadata: Additional JSON metadata
    
    Returns:
        Log entry ID or None if failed
    """
    try:
        from db import get_db
        
        db = get_db()
        
        log_entry = {
            "action_type": action_type,
            "message": message,
            "user_phone": user_phone,
            "channel": channel
        }
        
        result = db.table("logs").insert(log_entry).execute()
        
        # Also print to console with icon
        icon = ACTION_ICONS.get(action_type, "📝")
        print(f"{icon} [{action_type.upper()}] {message}")
        
        return result.data[0]["id"] if result.data else None
        
    except Exception as e:
        print(f"❌ [LOG ERROR] Failed to log: {str(e)}")
        return None


def log_invoice_created(
    invoice_number: str,
    customer_name: str,
    amount: float,
    user_phone: Optional[str] = None
):
    """Log invoice creation"""
    log_action(
        ActionType.INVOICE_CREATED,
        f"Invoice {invoice_number} created for {customer_name}: ₹{amount:,.2f}",
        user_phone=user_phone,
        channel="system"
    )


def log_invoice_paid(
    invoice_number: str,
    customer_name: str,
    amount: float,
    user_phone: Optional[str] = None
):
    """Log invoice payment"""
    log_action(
        ActionType.INVOICE_PAID,
        f"Invoice {invoice_number} paid by {customer_name}: ₹{amount:,.2f}",
        user_phone=user_phone,
        channel="system"
    )


def log_reminder_sent(
    customer_name: str,
    amount: float,
    channel: str,
    user_phone: Optional[str] = None
):
    """Log reminder sent"""
    log_action(
        ActionType.REMINDER_SENT,
        f"Reminder sent to {customer_name} for ₹{amount:,.2f} via {channel}",
        user_phone=user_phone,
        channel=channel
    )


def log_inventory_updated(
    item_name: str,
    previous_qty: int,
    new_qty: int,
    operation: str,
    user_phone: Optional[str] = None
):
    """Log inventory update"""
    action_type = ActionType.INVENTORY_UPDATED
    
    # Check for alerts
    if new_qty == 0:
        action_type = ActionType.INVENTORY_OUT_OF_STOCK
    elif new_qty <= 10:  # Default threshold
        action_type = ActionType.INVENTORY_LOW_STOCK
    
    log_action(
        action_type,
        f"{item_name}: {previous_qty} → {new_qty} ({operation})",
        user_phone=user_phone,
        channel="system"
    )


def log_action_confirmed(
    action_type_confirmed: str,
    summary: str,
    user_phone: Optional[str] = None
):
    """Log user confirmation"""
    log_action(
        ActionType.ACTION_CONFIRMED,
        f"Confirmed: {action_type_confirmed} - {summary}",
        user_phone=user_phone,
        channel="system"
    )


def log_action_cancelled(
    action_type_cancelled: str,
    reason: str = "User cancelled",
    user_phone: Optional[str] = None
):
    """Log action cancellation"""
    log_action(
        ActionType.ACTION_CANCELLED,
        f"Cancelled: {action_type_cancelled} - {reason}",
        user_phone=user_phone,
        channel="system"
    )


def log_error(
    error_message: str,
    source: str = "system",
    user_phone: Optional[str] = None
):
    """Log system error"""
    log_action(
        ActionType.SYSTEM_ERROR,
        f"[{source}] {error_message}",
        user_phone=user_phone,
        channel="system"
    )


# ============================================
# API ENDPOINTS (for Dashboard)
# ============================================

@router.get("/")
async def get_logs(
    limit: int = Query(100, le=500),
    action_type: Optional[str] = None,
    user_phone: Optional[str] = None,
    channel: Optional[str] = None,
    start_date: Optional[str] = None,
    end_date: Optional[str] = None
):
    """
    Get logs with optional filters
    Dashboard polls this endpoint for live updates
    """
    from db import get_db
    
    db = get_db()
    query = db.table("logs").select("*").order("created_at", desc=True)
    
    if action_type:
        query = query.eq("action_type", action_type)
    
    if user_phone:
        query = query.eq("user_phone", user_phone)
    
    if channel:
        query = query.eq("channel", channel)
    
    if start_date:
        query = query.gte("created_at", start_date)
    
    if end_date:
        query = query.lte("created_at", end_date)
    
    result = query.limit(limit).execute()
    
    # Add icons to logs
    logs = []
    for log in result.data or []:
        log["icon"] = ACTION_ICONS.get(log["action_type"], "📝")
        logs.append(log)
    
    return {
        "logs": logs,
        "count": len(logs),
        "filters": {
            "action_type": action_type,
            "user_phone": user_phone,
            "channel": channel
        }
    }


@router.get("/latest")
async def get_latest_logs(count: int = 10):
    """Get latest N logs for dashboard widget"""
    from db import get_db
    
    db = get_db()
    result = db.table("logs")\
        .select("*")\
        .order("created_at", desc=True)\
        .limit(count)\
        .execute()
    
    logs = []
    for log in result.data or []:
        log["icon"] = ACTION_ICONS.get(log["action_type"], "📝")
        logs.append(log)
    
    return {"logs": logs}


@router.get("/today")
async def get_today_logs():
    """Get all logs from today"""
    from db import get_db
    
    db = get_db()
    today = str(date.today())
    
    result = db.table("logs")\
        .select("*")\
        .gte("created_at", today)\
        .order("created_at", desc=True)\
        .execute()
    
    logs = result.data or []
    
    # Group by action type
    by_type = {}
    for log in logs:
        t = log["action_type"]
        by_type[t] = by_type.get(t, 0) + 1
    
    return {
        "date": today,
        "total": len(logs),
        "by_type": by_type,
        "logs": logs
    }


@router.get("/summary")
async def get_logs_summary(days: int = 7):
    """Get summary of logs for the past N days"""
    from db import get_db
    
    db = get_db()
    start_date = str(date.today() - timedelta(days=days))
    
    result = db.table("logs")\
        .select("action_type, created_at")\
        .gte("created_at", start_date)\
        .execute()
    
    logs = result.data or []
    
    # Group by type
    by_type = {}
    for log in logs:
        t = log["action_type"]
        by_type[t] = by_type.get(t, 0) + 1
    
    # Group by day
    by_day = {}
    for log in logs:
        day = log["created_at"][:10]
        by_day[day] = by_day.get(day, 0) + 1
    
    return {
        "period_days": days,
        "total_logs": len(logs),
        "by_type": by_type,
        "by_day": by_day,
        "most_common": max(by_type, key=by_type.get) if by_type else None
    }


@router.get("/user/{user_phone}")
async def get_user_logs(user_phone: str, limit: int = 50):
    """Get all logs for a specific user"""
    from db import get_db
    
    db = get_db()
    result = db.table("logs")\
        .select("*")\
        .eq("user_phone", user_phone)\
        .order("created_at", desc=True)\
        .limit(limit)\
        .execute()
    
    return {
        "user_phone": user_phone,
        "logs": result.data or [],
        "count": len(result.data or [])
    }


@router.get("/action_types")
async def get_action_types():
    """Get all possible action types with their icons"""
    return {
        "action_types": [
            {"type": at.value, "icon": ACTION_ICONS.get(at.value, "📝")}
            for at in ActionType
        ]
    }


# ============================================
# AUDIT TRAIL HELPERS
# ============================================

async def get_audit_trail(
    entity_type: str,  # invoice, customer, inventory
    entity_id: str,
    limit: int = 20
) -> List[Dict]:
    """Get audit trail for a specific entity"""
    from db import get_db
    
    db = get_db()
    
    # Search logs that mention this entity
    result = db.table("logs")\
        .select("*")\
        .ilike("message", f"%{entity_id}%")\
        .order("created_at", desc=True)\
        .limit(limit)\
        .execute()
    
    return result.data or []


async def export_logs_csv(
    start_date: str,
    end_date: str
) -> str:
    """Export logs to CSV format"""
    from db import get_db
    import csv
    from io import StringIO
    
    db = get_db()
    
    result = db.table("logs")\
        .select("*")\
        .gte("created_at", start_date)\
        .lte("created_at", end_date)\
        .order("created_at")\
        .execute()
    
    output = StringIO()
    writer = csv.writer(output)
    
    # Header
    writer.writerow(["ID", "Timestamp", "Action Type", "Message", "User Phone", "Channel"])
    
    # Data
    for log in result.data or []:
        writer.writerow([
            log["id"],
            log["created_at"],
            log["action_type"],
            log["message"],
            log.get("user_phone", ""),
            log.get("channel", "")
        ])
    
    return output.getvalue()


@router.get("/export")
async def export_logs(
    start_date: str,
    end_date: str,
    format: str = "json"
):
    """Export logs in JSON or CSV format"""
    if format == "csv":
        csv_data = await export_logs_csv(start_date, end_date)
        from fastapi.responses import Response
        return Response(
            content=csv_data,
            media_type="text/csv",
            headers={"Content-Disposition": f"attachment; filename=logs_{start_date}_{end_date}.csv"}
        )
    else:
        from db import get_db
        db = get_db()
        result = db.table("logs")\
            .select("*")\
            .gte("created_at", start_date)\
            .lte("created_at", end_date)\
            .order("created_at")\
            .execute()
        return {"logs": result.data or []}
