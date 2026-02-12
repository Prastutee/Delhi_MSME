"""
Ledger Management and Payment Reminders
Detect overdue invoices and send proactive Hinglish reminders
"""
from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from typing import Optional, List, Dict
from datetime import datetime, date, timedelta
import random

router = APIRouter()

# ============================================
# MODELS
# ============================================

class ReminderDraft(BaseModel):
    invoice_id: str
    customer_name: str
    customer_phone: str
    amount: float
    days_overdue: int
    reminder_message: str
    channel: str = "whatsapp"


class TransactionCreate(BaseModel):
    customer_phone: str
    customer_name: str
    amount: float
    txn_type: str  # credit, debit, payment, refund
    description: Optional[str] = ""


# ============================================
# HINGLISH REMINDER TEMPLATES
# ============================================

REMINDER_TEMPLATES = [
    "🙏 Namaste {name} ji! ₹{amount} ka payment pending hai. Jab convenient ho, bhej dena. Dhanyavaad!",
    "Bhaiya {name}, ₹{amount} baaki hai. Kal tak bhej dena please 🙏",
    "{name} ji, friendly reminder - ₹{amount} ka payment due hai. Kab tak mil jayega?",
    "🔔 {name} bhai, ₹{amount} pending hai ({days} din ho gaye). Jaldi settle kar dena 🙏",
    "Namaste {name}! Aapka ₹{amount} ka payment pending hai. Please check karein 🙏",
    "{name} ji, bass yaad dila raha tha - ₹{amount} baaki hai from {invoice}. Thanks! 🙏",
]

URGENT_TEMPLATES = [
    "⚠️ {name} ji, ₹{amount} ka payment {days} din se pending hai. Urgent attention required!",
    "🚨 {name} bhai, ₹{amount} bohot overdue ho gaya ({days} days). Please settle ASAP 🙏",
    "❗ {name} ji, payment reminder - ₹{amount} ({days} din overdue). Kindly clear soon.",
]


def generate_reminder_message(
    customer_name: str,
    amount: float,
    days_overdue: int,
    invoice_number: str = ""
) -> str:
    """Generate a polite Hinglish reminder message"""
    
    # Use urgent template if very overdue
    if days_overdue > 15:
        template = random.choice(URGENT_TEMPLATES)
    else:
        template = random.choice(REMINDER_TEMPLATES)
    
    return template.format(
        name=customer_name,
        amount=f"{amount:,.0f}",
        days=days_overdue,
        invoice=invoice_number or "recent order"
    )


# ============================================
# OVERDUE DETECTION
# ============================================

async def get_overdue_invoices(days_threshold: int = 7) -> List[Dict]:
    """
    Get all invoices that are overdue by more than X days
    
    Returns list of overdue invoices with customer details
    """
    from db import get_db, log_event
    
    db = get_db()
    
    # Calculate cutoff date
    cutoff_date = (date.today() - timedelta(days=days_threshold)).isoformat()
    
    # Get overdue invoices
    result = db.table("invoices")\
        .select("*, customers(*)")\
        .in_("status", ["pending", "overdue"])\
        .lt("due_date", str(date.today()))\
        .order("due_date")\
        .execute()
    
    overdue = []
    for inv in result.data or []:
        due = datetime.strptime(str(inv["due_date"]), "%Y-%m-%d").date()
        days_overdue = (date.today() - due).days
        
        if days_overdue >= days_threshold:
            customer = inv.get("customers", {})
            overdue.append({
                "invoice_id": inv["id"],
                "invoice_number": inv.get("invoice_number", ""),
                "customer_id": inv.get("customer_id"),
                "customer_name": customer.get("name", "Customer"),
                "customer_phone": customer.get("phone", ""),
                "amount": float(inv["amount"]),
                "due_date": str(inv["due_date"]),
                "days_overdue": days_overdue,
                "status": inv["status"]
            })
    
    return overdue


async def generate_reminder_drafts(days_threshold: int = 7) -> List[ReminderDraft]:
    """
    Generate reminder drafts for all overdue invoices
    
    Returns list of ReminderDraft objects ready for approval
    """
    overdue = await get_overdue_invoices(days_threshold)
    
    drafts = []
    for inv in overdue:
        message = generate_reminder_message(
            customer_name=inv["customer_name"],
            amount=inv["amount"],
            days_overdue=inv["days_overdue"],
            invoice_number=inv.get("invoice_number", "")
        )
        
        drafts.append(ReminderDraft(
            invoice_id=inv["invoice_id"],
            customer_name=inv["customer_name"],
            customer_phone=inv["customer_phone"],
            amount=inv["amount"],
            days_overdue=inv["days_overdue"],
            reminder_message=message
        ))
    
    return drafts


# ============================================
# SEND REMINDERS
# ============================================

async def send_reminder(
    customer_phone: str,
    message: str,
    channel: str = "whatsapp",
    invoice_id: Optional[str] = None
) -> Dict:
    """
    Send a reminder via WhatsApp or Telegram
    
    Returns status of the send operation
    """
    from db import log_event, get_db
    
    try:
        if channel == "whatsapp":
            from tools.whatsapp_twilio import send_text
            result = await send_text(customer_phone, message)
        else:
            from tools.telegram_bot import send_text
            result = await send_text(customer_phone, message)
        
        # Log the reminder
        log_event(
            "reminder",
            f"Sent reminder to {customer_phone}: {message[:50]}...",
            user_phone=customer_phone,
            channel=channel
        )
        
        # Update invoice status note
        if invoice_id:
            db = get_db()
            current = db.table("invoices").select("notes").eq("id", invoice_id).single().execute()
            notes = current.data.get("notes", "") if current.data else ""
            new_note = f"{notes}\n[{datetime.now().strftime('%Y-%m-%d')}] Reminder sent"
            db.table("invoices").update({"notes": new_note.strip()}).eq("id", invoice_id).execute()
        
        return {"success": True, "message": "Reminder sent", "result": result}
        
    except Exception as e:
        log_event("error", f"Reminder send failed: {str(e)}")
        return {"success": False, "error": str(e)}


async def send_bulk_reminders(drafts: List[ReminderDraft], channel: str = "whatsapp") -> Dict:
    """Send reminders to multiple customers"""
    results = []
    
    for draft in drafts:
        result = await send_reminder(
            customer_phone=draft.customer_phone,
            message=draft.reminder_message,
            channel=channel,
            invoice_id=draft.invoice_id
        )
        results.append({
            "customer": draft.customer_name,
            "phone": draft.customer_phone,
            "success": result.get("success", False)
        })
    
    sent = sum(1 for r in results if r["success"])
    
    return {
        "total": len(drafts),
        "sent": sent,
        "failed": len(drafts) - sent,
        "results": results
    }


# ============================================
# API ENDPOINTS
# ============================================

@router.get("/daily_check")
async def daily_check(days_threshold: int = 7):
    """
    Daily check endpoint - Returns overdue invoices with reminder drafts
    
    Use this to review pending reminders before sending
    """
    from db import log_event
    
    log_event("system", "Running daily overdue check")
    
    overdue = await get_overdue_invoices(days_threshold)
    drafts = await generate_reminder_drafts(days_threshold)
    
    # Summary statistics
    total_overdue = sum(inv["amount"] for inv in overdue)
    
    return {
        "check_date": str(date.today()),
        "days_threshold": days_threshold,
        "summary": {
            "total_overdue_count": len(overdue),
            "total_overdue_amount": total_overdue,
            "oldest_overdue_days": max((inv["days_overdue"] for inv in overdue), default=0)
        },
        "overdue_invoices": overdue,
        "reminder_drafts": [d.dict() for d in drafts]
    }


@router.post("/send_reminder")
async def send_single_reminder(
    invoice_id: str,
    channel: str = "whatsapp",
    custom_message: Optional[str] = None
):
    """Send a reminder for a specific invoice"""
    from db import get_db
    
    db = get_db()
    
    # Get invoice details
    result = db.table("invoices").select("*, customers(*)").eq("id", invoice_id).single().execute()
    
    if not result.data:
        raise HTTPException(status_code=404, detail="Invoice not found")
    
    inv = result.data
    customer = inv.get("customers", {})
    
    # Calculate days overdue
    due = datetime.strptime(str(inv["due_date"]), "%Y-%m-%d").date()
    days_overdue = (date.today() - due).days
    
    # Generate or use custom message
    if custom_message:
        message = custom_message
    else:
        message = generate_reminder_message(
            customer_name=customer.get("name", "Customer"),
            amount=float(inv["amount"]),
            days_overdue=max(0, days_overdue),
            invoice_number=inv.get("invoice_number", "")
        )
    
    # Send reminder
    result = await send_reminder(
        customer_phone=customer.get("phone", ""),
        message=message,
        channel=channel,
        invoice_id=invoice_id
    )
    
    return result


@router.post("/send_bulk_reminders")
async def send_all_reminders(
    channel: str = "whatsapp",
    days_threshold: int = 7
):
    """Send reminders to all overdue customers"""
    drafts = await generate_reminder_drafts(days_threshold)
    
    if not drafts:
        return {"message": "No overdue invoices found", "sent": 0}
    
    result = await send_bulk_reminders(drafts, channel)
    
    return result


@router.get("/customer/{customer_id}/ledger")
async def get_customer_ledger(customer_id: str, limit: int = 50):
    """Get transaction ledger for a customer"""
    from db import get_db, get_customer_balance
    
    db = get_db()
    
    # Get customer info
    customer = db.table("customers").select("*").eq("id", customer_id).single().execute()
    if not customer.data:
        raise HTTPException(status_code=404, detail="Customer not found")
    
    # Get transactions
    transactions = db.table("transactions")\
        .select("*")\
        .eq("customer_id", customer_id)\
        .order("created_at", desc=True)\
        .limit(limit)\
        .execute()
    
    # Get balance
    balance = await get_customer_balance(customer_id)
    
    return {
        "customer": customer.data,
        "balance": balance,
        "transactions": transactions.data or []
    }


@router.post("/transaction")
async def create_transaction(txn: TransactionCreate):
    """Create a new transaction"""
    from db import get_or_create_customer, add_transaction, log_event
    
    customer = await get_or_create_customer(txn.customer_phone, txn.customer_name)
    
    result = await add_transaction(
        customer_id=customer["id"],
        amount=txn.amount,
        txn_type=txn.txn_type,
        description=txn.description
    )
    
    log_event("ledger", f"Transaction: {txn.txn_type} ₹{txn.amount} for {txn.customer_name}")
    
    return {"transaction": result, "customer": customer}


@router.get("/summary")
async def get_ledger_summary():
    """Get overall ledger summary"""
    from db import get_db
    
    db = get_db()
    
    # Get all transactions
    transactions = db.table("transactions").select("type, amount").execute().data or []
    
    # Calculate totals
    credits = sum(t["amount"] for t in transactions if t["type"] in ["credit"])
    payments = sum(t["amount"] for t in transactions if t["type"] in ["payment"])
    debits = sum(t["amount"] for t in transactions if t["type"] in ["debit", "refund"])
    
    # Get overdue count
    overdue = await get_overdue_invoices(0)
    
    return {
        "total_credits": credits,
        "total_payments": payments,
        "total_debits": debits,
        "outstanding": credits - payments,
        "overdue_count": len(overdue),
        "overdue_amount": sum(inv["amount"] for inv in overdue)
    }
