"""
Supabase database client and helper functions
Extended with deterministic helpers for kirana workflows
"""
from supabase import create_client, Client
from datetime import datetime, date, timedelta
from typing import Optional, List, Dict, Any
import json

# Lazy import to avoid circular dependency
_client: Optional[Client] = None

def get_db() -> Client:
    """Get Supabase client singleton"""
    global _client
    if _client is None:
        from config import settings
        if settings:
            _client = create_client(settings.supabase_url, settings.supabase_key)
        else:
            raise Exception("Settings not initialized - check environment variables")
    return _client

async def init_db():
    """Initialize database connection"""
    try:
        client = get_db()
        result = client.table("customers").select("id").limit(1).execute()
        # Also check if debug_logs exists (soft check)
        try:
            client.table("debug_logs").select("id").limit(1).execute()
        except:
            print("⚠️ 'debug_logs' table missing. Run schema.sql update.")
            
        print("✅ Supabase connected")
        return True
    except Exception as e:
        print(f"⚠️ Supabase connection pending: {e}")
        return False


# ============================================
# CUSTOMER OPERATIONS
# ============================================

async def get_or_create_customer(phone: str, name: str = "") -> Dict:
    """Get customer by phone or create if not exists"""
    db = get_db()
    
    result = db.table("customers").select("*").eq("phone", phone).execute()
    
    if result.data:
        existing = result.data[0]
        if name and len(name) > 1 and existing["name"].startswith("Customer"):
             db.table("customers").update({"name": name}).eq("id", existing["id"]).execute()
             existing["name"] = name
        return existing
    
    new_customer = db.table("customers").insert({
        "phone": phone,
        "name": name or f"Customer {phone[-4:]}"
    }).execute()
    
    return new_customer.data[0] if new_customer.data else None

async def create_customer(name: str, phone: Optional[str] = None) -> Optional[Dict]:
    """Create a new customer (Auto-generate phone if missing)"""
    db = get_db()
    
    # Generate placeholder phone if missing (Required by Schema)
    if not phone:
        import uuid
        phone = f"gen-{uuid.uuid4().hex[:8]}"
        
    try:
        new_customer = db.table("customers").insert({
            "name": name,
            "phone": phone
        }).execute()
        return new_customer.data[0] if new_customer.data else None
    except Exception as e:
        print(f"[!] Failed to create customer {name}: {e}")
        return None

async def find_customer_by_name(name: str) -> Optional[Dict]:
    """Find customer by name (fuzzy match)"""
    db = get_db()
    result = db.table("customers").select("*").ilike("name", f"%{name}%").execute()
    return result.data[0] if result.data else None

async def get_customer(phone: str) -> Optional[Dict]:
    """Get customer by phone"""
    db = get_db()
    result = db.table("customers").select("*").eq("phone", phone).execute()
    return result.data[0] if result.data else None


# ============================================
# SUPPLIER OPERATIONS (NEW)
# ============================================

async def find_supplier_for_item(item_name: str) -> Optional[Dict]:
    """Get supplier for an item"""
    db = get_db()
    result = db.table("suppliers").select("*").ilike("item_name", f"%{item_name}%").execute()
    return result.data[0] if result.data else None


# ============================================
# INVENTORY OPERATIONS (Extended)
# ============================================

async def get_inventory_item(item_name: str) -> Optional[Dict]:
    """Search for inventory item by name"""
    db = get_db()
    result = db.table("inventory").select("*").ilike("item_name", f"%{item_name}%").execute()
    return result.data[0] if result.data else None

async def get_unit_price(item_name: str) -> Optional[float]:
    """Get price from inventory (deterministic - never guess)"""
    item = await get_inventory_item(item_name)
    if item and item.get("price"):
        return float(item["price"])
    return None

async def set_unit_price(item_name: str, price: float) -> Dict:
    """Set price in inventory"""
    db = get_db()
    item = await get_inventory_item(item_name)
    
    if item:
        db.table("inventory").update({"price": price}).eq("id", item["id"]).execute()
        return {"item": item_name, "price": price, "updated": True}
    else:
        # Create new item with price
        db.table("inventory").insert({
            "item_name": item_name,
            "quantity": 0,
            "price": price
        }).execute()
        return {"item": item_name, "price": price, "created": True}

async def update_inventory(item_name: str, quantity_change: int, operation: str = "set", user_phone: Optional[str] = None) -> Dict:
    """
    Update inventory quantity (Centralized Logic)
    
    Args:
        item_name: Name of item (fuzzy match)
        quantity_change: Amount to change (or set)
        operation: 'add', 'subtract', 'set'
        user_phone: Optional phone for logging
        
    Returns:
        Dict with previous/new values and item details
    """
    db = get_db()
    
    # 1. FIND ITEM
    item = db.table("inventory").select("*").ilike("item_name", f"%{item_name}%").execute()
    
    if item.data:
        current = item.data[0]
        item_id = current["id"]
        current_qty = current["quantity"]
        
        # 2. CALCULATE NEW QUANTITY
        if operation == "add":
            new_qty = current_qty + quantity_change
            action_desc = f"Added {quantity_change}"
        elif operation == "subtract":
            new_qty = max(0, current_qty - quantity_change)
            action_desc = f"Removed {quantity_change}"
        else: # set
            new_qty = quantity_change
            action_desc = f"Set to {quantity_change}"
        
        # 3. UPDATE DB
        # TODO: Use RPC 'increment_inventory' if race conditions become critical
        # For now, we trust the sequential nature of single-user chat or low-traffic dashboard
        db.table("inventory").update({
            "quantity": new_qty,
            "updated_at": datetime.now().isoformat()
        }).eq("id", item_id).execute()
        
        # 4. CENTRALIZED LOGGING
        log_event(
            "inventory",
            f"{current['item_name']}: {action_desc} (was {current_qty}, now {new_qty})",
            user_phone=user_phone
        )
        
        return {
            "success": True,
            "item_name": current["item_name"], 
            "previous": current_qty, 
            "new": new_qty, 
            "item_id": item_id,
            "unit": current.get("unit", "pcs"),
            "price": current.get("price", 0)
        }
    else:
        # Create new item (Auto-create logic)
        if operation == "subtract":
             return {"success": False, "error": f"Item '{item_name}' not found so cannot subtract."}
             
        final_qty = quantity_change
        result = db.table("inventory").insert({
            "item_name": item_name,
            "quantity": final_qty,
            "unit": "pcs",
            "price": 0,
            "low_stock_threshold": 10
        }).execute()
        
        new_item = result.data[0] if result.data else {}
        
        log_event(
            "inventory",
            f"Created new item: {item_name} (Qty: {final_qty})",
            user_phone=user_phone
        )
        
        return {
            "success": True,
            "item_name": item_name,
            "previous": 0,
            "new": final_qty,
            "item_id": new_item.get("id"),
            "unit": "pcs",
            "price": 0
        }

async def check_low_stock(item_name: str) -> Optional[Dict]:
    """Check if item is below threshold, return alert info if so"""
    item = await get_inventory_item(item_name)
    if not item:
        return None
    
    threshold = item.get("low_stock_threshold", 10)
    current_qty = item.get("quantity", 0)
    
    if current_qty <= threshold:
        supplier = await find_supplier_for_item(item_name)
        return {
            "item_name": item["item_name"],
            "quantity": current_qty,
            "threshold": threshold,
            "supplier": supplier
        }
    return None

async def get_low_stock_items(threshold: int = 10) -> List[Dict]:
    """Get items below stock threshold"""
    db = get_db()
    result = db.table("inventory").select("*").lte("quantity", threshold).execute()
    return result.data or []

async def list_inventory() -> List[Dict]:
    """Get all inventory items"""
    db = get_db()
    result = db.table("inventory").select("*").order("item_name").execute()
    return result.data or []


# ============================================
# TRANSACTION OPERATIONS (Extended)
# ============================================

async def add_transaction(
    customer_id: Optional[str],
    amount: float,
    txn_type: str,
    description: str = "",
    invoice_id: Optional[str] = None,
    item_name: Optional[str] = None,
    quantity: Optional[int] = None
) -> Dict:
    """Add a transaction to the ledger"""
    db = get_db()
    
    txn_data = {
        "amount": amount,
        "type": txn_type,
        "description": description
    }
    
    if customer_id:
        txn_data["customer_id"] = customer_id
    if invoice_id:
        txn_data["invoice_id"] = invoice_id
    if item_name:
        txn_data["item_name"] = item_name
    if quantity:
        txn_data["quantity"] = quantity
    
    result = db.table("transactions").insert(txn_data).execute()
    return result.data[0] if result.data else None

async def get_customer_balance(customer_id: str) -> Dict:
    """Get customer's balance (Credit - Payments)"""
    db = get_db()
    
    result = db.table("transactions").select("*").eq("customer_id", customer_id).execute()
    transactions = result.data or []
    
    # Credits: money owed BY customer (sale_credit, credit)
    credits = sum(t["amount"] for t in transactions if t["type"] in ["credit", "sale_credit"])
    
    # Debits: money paid BY customer (payment)
    debits = sum(t["amount"] for t in transactions if t["type"] in ["payment", "debit"])
    
    return {
        "customer_id": customer_id,
        "total_credits": credits,
        "total_debits": debits,
        "balance": credits - debits
    }


# ============================================
# INVOICE OPERATIONS
# ============================================

async def create_invoice(
    customer_id: str,
    amount: float,
    due_date: Optional[date] = None,
    notes: str = ""
) -> Dict:
    """Create a new invoice"""
    db = get_db()
    
    today = datetime.now()
    invoice_number = f"INV-{today.strftime('%Y%m%d')}-{today.strftime('%H%M%S')}"
    
    if due_date is None:
        due_date = (today + timedelta(days=7)).date()
    
    invoice_data = {
        "customer_id": customer_id,
        "invoice_number": invoice_number,
        "amount": amount,
        "status": "pending",
        "due_date": str(due_date),
        "notes": notes
    }
    
    result = db.table("invoices").insert(invoice_data).execute()
    return result.data[0] if result.data else None

async def get_invoice(invoice_id: str) -> Optional[Dict]:
    """Get invoice by ID"""
    db = get_db()
    result = db.table("invoices").select("*, customers(*)").eq("id", invoice_id).single().execute()
    return result.data

async def mark_paid(invoice_id: str) -> Dict:
    """Mark invoice as paid"""
    db = get_db()
    db.table("invoices").update({"status": "paid"}).eq("id", invoice_id).execute()
    return {"status": "paid", "invoice_id": invoice_id}

async def list_invoices(customer_id: Optional[str] = None, status: Optional[str] = None) -> List[Dict]:
    """List invoices with optional filters"""
    db = get_db()
    query = db.table("invoices").select("*, customers(*)")
    
    if customer_id:
        query = query.eq("customer_id", customer_id)
    if status:
        query = query.eq("status", status)
    
    result = query.order("created_at", desc=True).execute()
    return result.data or []


# ============================================
# LOGGING OPERATIONS
# ============================================

def log_event(
    action_type: str,
    message: str,
    user_phone: Optional[str] = None,
    channel: Optional[str] = None
):
    """Log an event to the database"""
    try:
        db = get_db()
        db.table("logs").insert({
            "action_type": action_type,
            "message": message,
            "user_phone": user_phone,
            "channel": channel
        }).execute()
    except Exception as e:
        pass # print(f"⚠️ Failed to log event: {e}")
    
    icons = {
        "telegram": "[TEL]", "invoice": "[INV]", "payment": "[PAY]", 
        "inventory": "[INV]", "error": "[ERR]", "system": "[SYS]", "sale": "[SAL]"
    }
    icon = icons.get(action_type, "[LOG]")
    print(f"{icon} [{action_type.upper()}] {message}")

def log_business_event(
    action_type: str,
    message: str,
    user_phone: Optional[str] = None,
    channel: Optional[str] = None
):
    """Log a business-relevant event (User Facing)"""
    # FIX 4: Expanded ALLOWED_ACTIONS to include all valid business events
    ALLOWED_ACTIONS = [
        "sale_credit", "sale_paid", "payment", "purchase",
        "reminder_sent", "reminder_created", "payment_received",
        "inventory_update", "low_stock_alert", "error"
    ]
    
    if action_type not in ALLOWED_ACTIONS:
        log_debug_event("log_filter", f"Skipped unrecognized business action: {action_type}", message)
        return

    log_event(action_type, message, user_phone, channel)

def log_debug_event(
    error_source: str,
    error_message: str,
    raw_payload: Optional[str] = None
):
    """Log a technical/debug event (Developer Only)"""
    # Writes to debug_logs table ONLY
    try:
        db = get_db()
        # Use log_business_event if debug_logs fails
        db.table("debug_logs").insert({
            "error_source": error_source,
            "error_message": error_message,
            "raw_payload": str(raw_payload) if raw_payload else None
        }).execute()
        # Print to console for dev awareness
        print(f"[DEBUG] ({error_source}) {error_message}")
    except Exception as e:
        # Fallback to standard logs if debug_logs table is missing
        try:
            db.table("logs").insert({
                "action_type": "debug",
                "message": f"[{error_source}] {error_message}",
                "user_phone": "system"
            }).execute()
        except:
            pass
        print(f"[ERR] ({error_source}) {error_message}")

async def get_logs(limit: int = 100, action_type: Optional[str] = None) -> List[Dict]:
    """Get recent logs"""
    db = get_db()
    query = db.table("logs").select("*").order("created_at", desc=True).limit(limit)
    
    if action_type:
        query = query.eq("action_type", action_type)
    
    result = query.execute()
    return result.data or []


# ============================================
# PENDING ACTIONS (for confirmation flow)
# ============================================

async def store_pending_action(
    user_phone: str,
    action_type: str,
    action_data: Dict
) -> Dict:
    """Store a pending action awaiting user confirmation"""
    db = get_db()
    
    # Cancel any existing pending actions for this user
    db.table("pending_actions")\
        .update({"status": "cancelled"})\
        .eq("user_phone", user_phone)\
        .eq("status", "pending")\
        .execute()
    
    # Create new pending action
    result = db.table("pending_actions").insert({
        "user_phone": user_phone,
        "action_type": action_type,
        "action_json": action_data,
        "status": "pending"
    }).execute()
    
    return result.data[0] if result.data else None

async def fetch_pending_action(user_phone: str) -> Optional[Dict]:
    """Get the most recent pending action for a user"""
    db = get_db()
    
    result = db.table("pending_actions")\
        .select("*")\
        .eq("user_phone", user_phone)\
        .eq("status", "pending")\
        .order("created_at", desc=True)\
        .limit(1)\
        .execute()
    
    if result.data:
        return result.data[0]
    return None

async def confirm_pending_action(action_id: str) -> Optional[Dict]:
    """Confirm a pending action (Atomic Lock)"""
    db = get_db()
    # Only update if status is 'pending' to prevent double-confirmation
    result = db.table("pending_actions")\
        .update({"status": "confirmed"})\
        .eq("id", action_id)\
        .eq("status", "pending")\
        .execute()
    return result.data[0] if result.data else None

async def cancel_pending_action(action_id: str) -> Optional[Dict]:
    """Cancel a pending action (Atomic Lock)"""
    db = get_db()
    result = db.table("pending_actions")\
        .update({"status": "cancelled"})\
        .eq("id", action_id)\
        .eq("status", "pending")\
        .execute()
    return result.data[0] if result.data else None


# ============================================
# CHAT LOG OPERATIONS
# ============================================

async def log_chat(
    user_phone: str,
    channel: str,
    message: str,
    direction: str
):
    """Log a chat message"""
    try:
        db = get_db()
        db.table("chat_logs").insert({
            "user_phone": user_phone,
            "channel": channel,
            "message": message,
            "direction": direction
        }).execute()
    except Exception as e:
        print(f"⚠️ Failed to log chat: {e}")

async def get_chat_history(user_phone: str, limit: int = 20) -> List[Dict]:
    """Get chat history for a user"""
    db = get_db()
    result = db.table("chat_logs")\
        .select("*")\
        .eq("user_phone", user_phone)\
        .order("created_at", desc=True)\
        .limit(limit)\
        .execute()
    # FIX 7: Add missing return statement
    return result.data or []

# ============================================
# REMINDER OPERATIONS (New)
# ============================================

async def create_reminder(
    customer_id: str,
    message: str,
    days_due: int = 7
) -> Dict:
    """Create a new reminder — FIX 3: schema-safe insert, never omits message/status"""
    db = get_db()
    
    due_date = datetime.now() + timedelta(days=days_due)
    
    # Core fields that always exist in schema (defensive)
    # If scheduled_for is missing, try next_run
    core_fields_to_try = [
        {"customer_id": customer_id, "message": message, "status": "pending", "scheduled_for": due_date.isoformat()},
        {"customer_id": customer_id, "message": message, "status": "pending", "next_run": due_date.isoformat()},
        {"customer_id": customer_id, "message": message, "status": "pending"}
    ]
    
    for payload in core_fields_to_try:
        try:
            result = db.table("reminders").insert(payload).execute()
            if result.data: return result.data[0]
        except Exception:
            continue

    print(f"[!] Failed to create reminder for {customer_id}")
    return None

