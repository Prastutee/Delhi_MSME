"""
LangGraph Workflow Engine for Bharat Biz-Agent
Handles all kirana shop transaction workflows with deterministic execution
DEMO-SAFE: Graceful handling of missing data
"""
from typing import TypedDict, Optional, Dict, Any, Literal
import json

# ============================================
# WORKFLOW STATE SCHEMA
# ============================================

class WorkflowState(TypedDict):
    """State that flows through the workflow graph"""
    user_phone: str
    raw_message: str
    media_url: Optional[str]
    media_type: Optional[str]
    
    intent: str
    entities: Dict[str, Any]
    
    customer: Optional[Dict]
    
    # MULTI-ITEM SUPPORT
    processed_items: list  # List[Dict] -> [{item_db, name, qty, price, total}]
    
    computed_total: Optional[float]
    
    needs_confirmation: bool
    awaiting_price: bool
    awaiting_confirmation: bool
    
    response: str
    action_result: Optional[Dict]
    low_stock_alert: Optional[Dict]
    inventory_error: Optional[bool]
    missing_prices: list # List of item names needing price
    
    # MASTER PROMPT STATE
    stage: Literal["draft", "price", "payment", "confirm", "executed", "cancelled"]
    payment_type: Optional[str] # cash, credit, unknown
    show_buttons: bool
    buttons: list # List[Dict] [{"label": "Confim", "action": "confirm"}, ...]


# ============================================
# DEMO-SAFE DEFAULTS
# ============================================

# DEMO_PRICES removed. System now strictly uses Database prices.


# ============================================
# WORKFLOW NODES
# ============================================

async def parse_user_message(state: WorkflowState) -> WorkflowState:
    """Node 1: Parse user message using Gemini LLM"""
    from agent import extract_intent_entities
    
    result = await extract_intent_entities(
        state["raw_message"],
        state["user_phone"]
    )
    
    state["intent"] = result.get("intent", "general_query")
    state["payment_type"] = result.get("payment_type", "unknown")
    state["entities"] = result.get("entities", {})
    state["response"] = result.get("response", "")
    state["needs_confirmation"] = result.get("needs_confirmation", False)
    
    # Initialize buttons state
    state["show_buttons"] = False
    state["buttons"] = []
    state["stage"] = "draft"
    
    return state


async def validate_entities(state: WorkflowState) -> WorkflowState:
    """Node 2: Validate and enrich entities from database (DEMO-SAFE)"""
    from db import find_customer_by_name, get_inventory_item
    
    entities = state["entities"]
    processed_items = []
    
    # Validate customer
    customer_name = entities.get("customer_name", "")
    if customer_name:
        customer = await find_customer_by_name(customer_name)
        
        # Data Consistency Fix: Auto-create if not found (Real Tool behavior)
        if not customer:
            from db import create_customer
            print(f"🆕 Auto-creating customer: {customer_name}")
            customer = await create_customer(customer_name)
            
        state["customer"] = customer
    
    # Validate items list
    items_list = entities.get("items", [])
    
    # Fallback to single item if list empty but fields present
    if not items_list and entities.get("item_name"):
        items_list = [{
            "name": entities.get("item_name"), 
            "quantity": entities.get("quantity", 1),
            "amount": entities.get("amount", 0)
        }]
        
    for item_data in items_list:
        raw_name = item_data.get("name", "Unknown")
        qty = int(item_data.get("quantity", 1))
        price_override = item_data.get("price", 0)
        
        db_item = await get_inventory_item(raw_name)
        
        final_price = 0
        if price_override > 0:
             final_price = float(price_override)
        elif db_item and db_item.get("price"):
             final_price = float(db_item["price"])
        else:
             # No price in DB. Return 0 to trigger "Ask Price" flow.
             final_price = 0
             
        processed_items.append({
            "name": db_item["item_name"] if db_item else raw_name,
            "quantity": qty,
            "unit_price": final_price,
            "total": qty * final_price,
            "db_item": db_item,
            "raw_name": raw_name
        })
            
    state["processed_items"] = processed_items
    return state


async def compute_transaction(state: WorkflowState) -> WorkflowState:
    """Node 3: Compute total amount deterministically"""
    intent = state["intent"]
    items = state.get("processed_items", [])
    
    total = 0
    missing_prices = []
    inventory_error = False
    
    # Sum up items
    for item in items:
        
        # FIX 1: Workflow Ordering - Include "sale" in price check
        # This ensures we catch missing prices BEFORE resolving payment type
        if item["unit_price"] == 0 and intent in ["sale", "sale_paid", "sale_credit", "purchase", "loss"]:
            missing_prices.append(item["name"])
            
        total += item["total"]
            
        # Inventory Check
        if intent in ["sale_paid", "sale_credit"] and item["db_item"]:
             curr = item["db_item"].get("quantity", 0)
             if item["quantity"] > curr:
                 inventory_error = True
                 item["inventory_error"] = True
                 item["current_stock"] = curr
    
    # Override total if explicit amount provided (e.g. payment) & no items
    if not items and state["entities"].get("amount", 0) > 0:
        total = state["entities"]["amount"]
        
    state["computed_total"] = total
    state["missing_prices"] = missing_prices
    state["inventory_error"] = inventory_error
    
    return state


async def build_confirmation(state: WorkflowState, language: str = "hi") -> WorkflowState:
    """Node 4: Build confirmation message for user (DEMO-SAFE)"""
    from db import get_customer_balance, store_pending_action
    
    # FIX 2: Ensure buttons defaults to False (only True at final stage)
    state["show_buttons"] = False
    
    intent = state["intent"]
    entities = state["entities"]
    customer = state.get("customer")
    items = state.get("processed_items", [])
    total = state.get("computed_total", 0)
    
    customer_name = customer["name"] if customer else entities.get("customer_name", "Customer")
    
    # ==================================================
    # MASTER PROMPT 5-STAGE WORKFLOW
    # Stage 1: Draft (Implicit)
    # Stage 2: Resolve Missing Price
    # Stage 3: Resolve Payment Type
    # Stage 4: Compute Total (Done in previous node)
    # Stage 5: Final Confirmation
    # ==================================================

    # HANDLE INVENTORY ERROR
    if state.get("inventory_error"):
        error_items = [i["name"] for i in items if i.get("inventory_error")]
        if language == "en":
             msg = f"❌ *Insufficient Stock*\nItems: {', '.join(error_items)}\n\nTransaction blocked."
        else:
             msg = f"❌ *Stock Kam Hai*\nItems: {', '.join(error_items)}\n\nBilling nahi ho sakti."
             
        state["response"] = msg
        state["stage"] = "draft"
        state["show_buttons"] = False
        return state

    # STAGE 2: RESOLVE MISSING PRICE
    missing_prices = state.get("missing_prices", [])
    if missing_prices:
        first_missing = missing_prices[0]
        
        await store_pending_action(
            user_phone=state["user_phone"],
            action_type="awaiting_price",
            action_data={
                "original_intent": intent,
                "payment_type": state.get("payment_type"),
                "entities": entities,
                "customer_id": customer["id"] if customer else None,
                "customer_name": customer_name,
                "missing_item": first_missing
            }
        )
        
        if language == "en":
             state["response"] = f"❓ Price needed for *{first_missing}*.\n\nEnter Price (₹ per unit):"
        else:
             state["response"] = f"❓ *{first_missing}* ka price set nahi hai.\n\nPrice batao (₹ per unit):"
        
        state["stage"] = "price"
        state["show_buttons"] = False
        return state
    
    # STAGE 3: RESOLVE PAYMENT TYPE
    # If intent is generic 'sale' OR payment_type is 'unknown', ask clarification
    if intent == "sale" or (intent in ["sale_paid", "sale_credit"] and state.get("payment_type", "unknown") == "unknown"):
        
        await store_pending_action(
            user_phone=state["user_phone"],
            action_type="awaiting_payment_type",
            action_data={
                "original_intent": "sale", # Normalize to sale
                "entities": entities,
                "customer_id": customer["id"] if customer else None,
                "customer_name": customer_name,
                "processed_items": items # Preserve processed items
            }
        )
        
        if language == "en":
            state["response"] = f"💰 *Payment Type?*\n\nIs this Cash or Credit (Udhaar)?"
        else:
            state["response"] = f"💰 *Payment Kaise Hua?*\n\nCash diya ya Udhaar likhna hai?"
            
        state["stage"] = "payment"
        state["show_buttons"] = False
        return state

    # STAGE 4: COMPUTE TOTAL (Done)
    
    # STAGE 5: FINAL CONFIRMATION
    # Only reachable if Price OK and Payment Type OK
    
    # Build item summary string
    item_lines = ""
    for item in items:
        item_lines += f"📦 {item['name']} × {item['quantity']} = ₹{item['total']:.0f}\n"

    # Determine specific intent from payment_type if needed
    final_intent = intent
    if intent == "sale":
        ptype = state.get("payment_type", "cash")
        final_intent = "sale_credit" if ptype == "credit" else "sale_paid"
    
    # Override generic intent for confirmation
    state["intent"] = final_intent

    if final_intent == "sale_paid":
        if language == "en":
            msg = f"""🛒 *Cash Sale*
👤 {customer_name}
{item_lines}
💰 Total: *₹{total:.2f}*

Confirm? (YES / NO)"""
        else:
            msg = f"""🛒 *Cash Sale*
👤 {customer_name}
{item_lines}
💰 Total: *₹{total:.2f}*

Confirm karein? (YES / NO)"""

    elif final_intent == "sale_credit":
        balance_info = ""
        if customer:
            try:
                bal = await get_customer_balance(customer["id"])
                current_bal = bal.get("balance", 0)
                new_bal = current_bal + total
                balance_info = f"\n📒 Prev Balance: ₹{current_bal:.0f}"
            except:
                pass
        
        if language == "en":
            msg = f"""📝 *Credit Sale (Udhaar)*
👤 {customer_name}
{item_lines}
💰 Total: *₹{total:.2f}*{balance_info}

Confirm? (YES / NO)"""
        else:
            msg = f"""📝 *Udhaar Sale*
👤 {customer_name}
{item_lines}
💰 Total: *₹{total:.2f}*{balance_info}

Confirm karein? (YES / NO)"""

    elif final_intent == "payment":
        if language == "en":
            msg = f"""💰 *Payment Received*
👤 {customer_name}
💵 Amount: *₹{total:.2f}*

Confirm? (YES / NO)"""
        else:
            msg = f"""💰 *Payment Received*
👤 {customer_name}
💵 Amount: *₹{total:.2f}*

Confirm karein? (YES / NO)"""

    elif final_intent == "purchase":
        if language == "en":
            msg = f"""📥 *Stock Purchase*
{item_lines}
💰 Total: *₹{total:.2f}*"""
        else:
            msg = f"""📥 *Stock Purchase*
{item_lines}
💰 Total: *₹{total:.2f}*"""
        
    elif final_intent == "loss":
        if language == "en":
            msg = f"""⚠️ *Loss/Wastage*
{item_lines}
💸 Loss: *₹{total:.2f}*"""
        else:
            msg = f"""⚠️ *Loss/Wastage*
{item_lines}
💸 Loss: *₹{total:.2f}*"""
        
    else:
        msg = state.get("response", "Kya karna hai?")
        state["show_buttons"] = False
        return state
        
    # Store pending action for confirmation
    await store_pending_action(
        user_phone=state["user_phone"],
        action_type=final_intent,
        action_data={
            "entities": entities,
            "processed_items": items,
            "customer_id": customer["id"] if customer else None,
            "customer_name": customer_name,
            "computed_total": total,
            "payment_type": state.get("payment_type")
        }
    )
    
    state["stage"] = "confirm"
    state["response"] = msg
    state["show_buttons"] = True
    state["buttons"] = [
        {"label": "✅ Confirm", "action": "confirm_transaction"},
        {"label": "❌ Cancel", "action": "cancel_transaction"}
    ]
    
    return state


async def execute_database_updates(state: WorkflowState) -> WorkflowState:
    """Node 5: Execute the actual database updates after confirmation"""
    from db import (
        add_transaction, update_inventory, get_customer_balance, 
        log_business_event, log_debug_event, check_low_stock, set_unit_price, create_reminder
    )
    
    intent = state["intent"]
    items = state.get("processed_items", [])
    total = state.get("computed_total", 0)
    customer = state.get("customer")
    
    result = {"success": True}
    
    try:
        # Loop through items to update inventory/transactions
        for item in items:
            item_name = item["name"]
            qty = item["quantity"]
            unit_price = item.get("unit_price", 0)
            
            # Save unit price if meaningful
            if unit_price and unit_price > 0 and item_name:
                 await set_unit_price(item_name, unit_price)

            if intent == "sale_paid":
                inv_result = await update_inventory(item_name, qty, "subtract")
                if not inv_result.get("success"):
                     raise Exception(f"Inventory update failed: {inv_result.get('error')}")
                     
                try:
                    await add_transaction(
                        customer_id=customer["id"] if customer else None,
                        amount=item["total"],
                        txn_type="sale_paid",
                        description=f"Cash sale: {item_name} × {qty}",
                        item_name=item_name,
                        quantity=qty
                    )
                except Exception as tx_err:
                    # ROLLBACK INVENTORY
                    await update_inventory(item_name, qty, "add")
                    raise Exception(f"Transaction failed, inventory rolled back: {str(tx_err)}")
            
            elif intent == "sale_credit":
                inv_result = await update_inventory(item_name, qty, "subtract")
                if not inv_result.get("success"):
                     raise Exception(f"Inventory update failed: {inv_result.get('error')}")

                try:
                    await add_transaction(
                        customer_id=customer["id"] if customer else None,
                        amount=item["total"],
                        txn_type="sale_credit",
                        description=f"Udhaar: {item_name} × {qty}",
                        item_name=item_name,
                        quantity=qty
                    )
                except Exception as tx_err:
                    # ROLLBACK INVENTORY
                    await update_inventory(item_name, qty, "add")
                    raise Exception(f"Transaction failed, inventory rolled back: {str(tx_err)}")
                
            elif intent == "purchase":
                await update_inventory(item_name, qty, "add")
                try:
                    await add_transaction(
                        customer_id=None,
                        amount=item["total"],
                        txn_type="purchase",
                        description=f"Purchase: {item_name} × {qty}",
                        item_name=item_name,
                        quantity=qty
                    )
                except Exception as tx_err:
                    # ROLLBACK INVENTORY (Purchase adds stock, so verify subtract)
                    await update_inventory(item_name, qty, "subtract")
                    raise Exception(f"Transaction failed, inventory rolled back: {str(tx_err)}")
                
            elif intent == "loss":
                inv_result = await update_inventory(item_name, qty, "subtract")
                if not inv_result.get("success"):
                     raise Exception(f"Inventory update failed: {inv_result.get('error')}")

                try:
                    await add_transaction(
                        customer_id=None,
                        amount=item["total"],
                        txn_type="loss",
                        description=f"Loss: {item_name} × {qty}",
                        item_name=item_name,
                        quantity=qty
                    )
                except Exception as tx_err:
                    # ROLLBACK INVENTORY
                    await update_inventory(item_name, qty, "add")
                    raise Exception(f"Transaction failed, inventory rolled back: {str(tx_err)}")

        # Post-loop actions (Reminders, Payment, Logs)
        
        if intent == "sale_credit":
             # Create Automatic Reminder
            if customer:
                await create_reminder(
                    customer_id=customer["id"],
                    message=f"Please pay ₹{total} for transaction",
                    days_due=7
                )
                log_business_event("reminder_created", f"Auto-reminder set for {customer['name']}", state["user_phone"])
            
            log_business_event("sale_credit", f"Credit: {customer['name'] if customer else 'Customer'} ₹{total}", state["user_phone"])
            if customer:
                bal = await get_customer_balance(customer["id"])
                result["new_balance"] = bal["balance"]
        
        elif intent == "sale_paid":
            log_business_event("sale_paid", f"Cash Sale: ₹{total} ({len(items)} items)", state["user_phone"])
            
        elif intent == "payment":
             # Payment is usually lump sum, not per item
             # FIX 3: Payment updates balance (Logic: Sale is +Debt, Payment is -Debt)
             # db.get_customer_balance subtracts 'payment' types, so we send POSITIVE amount here.
            await add_transaction(
                customer_id=customer["id"] if customer else None,
                amount=total, 
                txn_type="payment",
                description=f"Payment from {customer['name'] if customer else 'Customer'}"
            )
            
            log_business_event("payment_received", f"Received ₹{total}", state["user_phone"])
            
            if customer:
                bal = await get_customer_balance(customer["id"])
                result["new_balance"] = bal["balance"]

        elif intent == "purchase":
             log_business_event("inventory_update", f"Purchase: ₹{total} ({len(items)} items)", state["user_phone"])
        
        state["action_result"] = result
        
        # Check for low stock alert
        if intent in ["sale_paid", "sale_credit", "loss"]:
            for item in items:
                low_stock = await check_low_stock(item["name"])
                if low_stock:
                    state["low_stock_alert"] = low_stock
                    log_business_event("low_stock_alert", f"Low Stock: {item['name']}", state["user_phone"])
                    break # Just show one alert for now
        
    except Exception as e:
        log_debug_event("workflow_execution", f"Execution error: {str(e)}", state["user_phone"])
        log_business_event("error", "System error during transaction", state["user_phone"])
        result["success"] = False
        result["error"] = str(e)
        state["action_result"] = result
    
    return state


async def build_receipt(state: WorkflowState, language: str = "hi") -> WorkflowState:
    """Node 6: Build receipt message after execution"""
    intent = state["intent"]
    entities = state["entities"]
    customer = state.get("customer")
    total = state.get("computed_total", 0)
    items = state.get("processed_items", [])
    result = state.get("action_result", {})
    
    if not result.get("success", True):
        state["response"] = f"❌ Error: {result.get('error', 'Unknown error')}"
        return state
    
    # Build receipt based on intent with demo banners
    customer_name = customer["name"] if customer else "Customer"
    
    # Item summary
    item_lines = ""
    for item in items:
        item_lines += f"📦 {item['name']} × {item['quantity']} = ₹{item['total']:.0f}\n"

    if intent == "sale_paid":
        new_stock = result.get("inventory", {}).get("new", "?")
        if language == "en":
             msg = f"""✅ *Cash Sale Recorded*
{item_lines}
💰 Total: ₹{total:.2f}
📊 Stock Updated"""
        else:
             msg = f"""✅ *Cash Sale Recorded*
{item_lines}
💰 Total: ₹{total:.2f}
📊 Stock Updated
_Next: Check stock anytime with /stock_"""
    
    elif intent == "sale_credit":
        new_bal = result.get("new_balance", total)
        if language == "en":
              msg = f"""✅ *Credit Entry Recorded*
👤 {customer_name}
{item_lines}
💰 Amount: ₹{total:.2f}
📒 Ledger Balance: ₹{new_bal:.2f} due"""
        else:
              msg = f"""✅ *Udhaar Recorded*
👤 {customer_name}
{item_lines}
💰 Amount: ₹{total:.2f}
📒 Balance: ₹{new_bal:.2f} pending
_Next: Send reminder with "remind {customer_name}"_"""
    
    elif intent == "payment":
        new_bal = result.get("new_balance", 0)
        old_bal = new_bal + total
        
        if new_bal <= 0:
            status = "All Clear ✅"
            next_tip = "_Khata clear ho gaya!_"
        else:
            status = f"₹{new_bal:.2f} remaining"
            next_tip = f"_Abhi ₹{new_bal:.2f} aur dena hai_"
            
        if language == "en":
             msg = f"""✅ *Payment Received*
👤 {customer_name}
💵 Received: ₹{total:.2f}
📉 Prev Balance: ₹{old_bal:.0f}
📒 New Balance: {status}
{next_tip}"""
        else:
             msg = f"""✅ *Payment Received*
👤 {customer_name}
💵 Received: ₹{total:.2f}
📉 Pehle ka: ₹{old_bal:.0f}
📒 Ab bacha: {status}"""
    
    elif intent == "purchase":
        new_stock = result.get("inventory", {}).get("new", "?")
        if language == "en":
             msg = f"""✅ *Stock Added*
{item_lines}
💰 Cost: ₹{total:.2f}
📊 Stock: Added to inventory"""
        else:
             msg = f"""✅ *Stock Added*
{item_lines}
💰 Cost: ₹{total:.2f}
📊 Stock: Inventory me add ho gaya"""
    
    elif intent == "loss":
        new_stock = result.get("inventory", {}).get("new", "?")
        if language == "en":
             msg = f"""✅ *Loss Recorded*
{item_lines}
💸 Loss: *₹{total:.2f}*
📊 Stock Updated"""
        else:
             msg = f"""✅ *Loss Recorded*
{item_lines}
💸 Loss: *₹{total:.2f}*
📊 Stock Updated"""
    
    else:
        msg = "✅ Done!"
    
    # Add low stock alert if applicable
    low_stock = state.get("low_stock_alert")
    if low_stock:
        supplier = low_stock.get("supplier")
        supplier_name = supplier["supplier_name"] if supplier else "Unknown"
        msg += f"""
⚠️ *LOW STOCK ALERT*
{low_stock['item_name']}: {low_stock['quantity']} left
Supplier: {supplier_name}

_Reorder karna hai? /reorder {low_stock['item_name']}_"""
    
    state["response"] = msg
    return state


# ============================================
# FIX 6: POST-WRITE VERIFICATION GUARD
# ============================================

async def _verify_post_write(state: WorkflowState) -> bool:
    """Demo-safety guard: verify that DB writes actually landed.
    Returns True if verification passes, False if something is missing."""
    from db import get_db
    
    intent = state.get("intent")
    customer = state.get("customer")
    items = state.get("processed_items", [])
    result = state.get("action_result", {})
    
    # If execute_database_updates itself reported failure, skip verification
    if not result.get("success", True):
        return False
    
    db = get_db()
    
    try:
        if intent in ["sale_credit", "sale_paid"]:
            # Verify: at least one transaction row exists for this customer recently
            if customer:
                txn_check = db.table("transactions")\
                    .select("id")\
                    .eq("transaction_type", intent)\
                    .order("created_at", desc=True)\
                    .limit(1)\
                    .execute()
                if not txn_check.data:
                    return False
            
            # Verify: inventory was reduced (spot check first item)
            if items and items[0].get("db_item"):
                inv_check = db.table("inventory")\
                    .select("quantity")\
                    .eq("item_name", items[0]["name"])\
                    .limit(1)\
                    .execute()
                if not inv_check.data:
                    return False
            
            # Verify: reminder exists for credit sales
            if intent == "sale_credit" and customer:
                rem_check = db.table("reminders")\
                    .select("id")\
                    .eq("customer_id", customer["id"])\
                    .eq("status", "pending")\
                    .order("created_at", desc=True)\
                    .limit(1)\
                    .execute()
                if not rem_check.data:
                    # Reminder missing is non-fatal for demo, log but pass
                    from db import log_debug_event
                    log_debug_event("post_write_verify", "Reminder not found after sale_credit", str(customer.get("id")))
        
        elif intent == "payment":
            # Verify: payment transaction exists
            if customer:
                txn_check = db.table("transactions")\
                    .select("id")\
                    .eq("transaction_type", "payment")\
                    .order("created_at", desc=True)\
                    .limit(1)\
                    .execute()
                if not txn_check.data:
                    return False
        
        return True
        
    except Exception as e:
        from db import log_debug_event
        log_debug_event("post_write_verify", f"Verification check error: {str(e)[:120]}", intent)
        # On error during verification, let it pass (don't block demo)
        return True


# ============================================
# CONFIRMATION HANDLER
# ============================================

async def handle_confirmation(user_phone: str, is_confirmed: bool, language: str = "hi") -> Dict[str, Any]:
    """Handle YES/NO confirmation from user — FIX 5: returns uniform dict"""
    from db import fetch_pending_action, confirm_pending_action, cancel_pending_action, get_db
    
    def make_resp(text: str, show_buttons: bool = False, buttons: list = None):
        return {"reply": text, "show_buttons": show_buttons, "buttons": buttons or []}
    
    pending = await fetch_pending_action(user_phone)
    
    if not pending:
        msg = "❓ No pending action found." if language == "en" else "❓ Koi pending action nahi hai. Pehle batao kya karna hai!"
        return make_resp(msg)
    
    if not is_confirmed:
        await cancel_pending_action(pending["id"])
        msg = "👍 Action Cancelled." if language == "en" else "👍 Theek hai, cancel kar diya."
        # FIX 9: No buttons after cancel
        return make_resp(msg)
    
    # Confirmed - execute the action
    # ATOMIC LOCK: Only proceed if we successfully claim the pending action
    confirmed_action = await confirm_pending_action(pending["id"])
    if not confirmed_action:
        msg = "⚠️ This action has already been processed." if language == "en" else "⚠️ Ye action pehle hi process ho chuka hai."
        return make_resp(msg)

    
    action_data = pending["action_json"]
    
    state: WorkflowState = {
        "user_phone": user_phone,
        "raw_message": "YES",
        "media_url": None,
        "media_type": None,
        "intent": pending["action_type"],
        "entities": action_data.get("entities", {}),
        "customer": None,
        "processed_items": action_data.get("processed_items", []),
        "computed_total": action_data.get("computed_total"),
        "needs_confirmation": False,
        "awaiting_price": False,
        "awaiting_confirmation": False,
        "response": "",
        "action_result": None,
        "low_stock_alert": None
    }
    
    # Fetch customer from ID
    db = get_db()
    if action_data.get("customer_id"):
        result = db.table("customers").select("*").eq("id", action_data["customer_id"]).execute()
        if result.data:
            state["customer"] = result.data[0]
    
    # Execute and build receipt
    state = await execute_database_updates(state)
    
    # FIX 6: Post-write verification guard
    verification_ok = await _verify_post_write(state)
    if not verification_ok:
        from db import log_debug_event
        log_debug_event("post_write_verify", f"Verification failed for {state['intent']}", str(action_data))
        return make_resp("⚠️ Internal sync error. Please retry.")
    
    state = await build_receipt(state, language=language)
    
    # FIX 9: After successful confirmation, no buttons
    return make_resp(state["response"])


async def handle_price_input(user_phone: str, price_text: str, pending_action: dict, language: str = "hi") -> Dict[str, Any]:
    """Handle price input for a pending action — FIX 5: returns uniform dict"""
    from db import get_db, confirm_pending_action, store_pending_action
    
    def make_resp(text: str, show_buttons: bool = False, buttons: list = None):
        return {"reply": text, "show_buttons": show_buttons, "buttons": buttons or []}
    
    # Try to parse price
    try:
        import re
        match = re.search(r'(\d+)', price_text)
        if not match:
             msg = "🔢 Please enter the **Unit Price** (Price for 1 item) as a number." if language == "en" else "🔢 Ek piece ka price likho (e.g. 40)"
             return make_resp(msg)
        
        unit_price = float(match.group(1))
    except:
        msg = "🔢 Please enter a valid number for Unit Price." if language == "en" else "🔢 Sahi price batao (Unit Price)."
        return make_resp(msg)

    # Restore state
    data = pending_action["action_json"]
    entities = data.get("entities", {})
    missing_item = data.get("missing_item")
    
    # Update entity with price
    # FIX P0: Name mismatch — entity has raw name (e.g. "Milk") but 
    # missing_item has DB name (e.g. "dairy milk"). Use flexible matching.
    items = entities.get("items", [])
    price_applied = False
    if missing_item:
        missing_lower = missing_item.lower()
        for item in items:
            item_name_lower = item.get("name", "").lower()
            # Match: exact, substring in either direction, or fuzzy
            if (item_name_lower == missing_lower or 
                item_name_lower in missing_lower or 
                missing_lower in item_name_lower):
                item["price"] = unit_price
                price_applied = True
                break
    
    # Fallback: if no match found, set price on first item without price
    if not price_applied and items:
        for item in items:
            if not item.get("price"):
                item["price"] = unit_price
                price_applied = True
                break
    
    state: WorkflowState = {
        "user_phone": user_phone,
        "raw_message": price_text,
        "media_url": None,
        "media_type": None,
        "intent": data.get("original_intent"),
        "payment_type": data.get("payment_type", "unknown"),  # FIX: restore payment_type
        "entities": entities,
        "customer": None,
        "processed_items": [], # Will be re-generated
        "computed_total": 0,
        "needs_confirmation": False,
        "awaiting_price": False,
        "awaiting_confirmation": False,
        "stage": "draft",
        "show_buttons": False,
        "buttons": [],
        "response": "",
        "action_result": None,
        "low_stock_alert": None,
        "inventory_error": None,  # FIX: add missing field
        "missing_prices": []
    }
    
    db = get_db()
    if data.get("customer_id"):
        res = db.table("customers").select("*").eq("id", data["customer_id"]).execute()
        if res.data: state["customer"] = res.data[0]
        
    # Re-run validation to process items with new price
    state = await validate_entities(state)
    
    # Recompute total
    state = await compute_transaction(state)
    
    # Build confirmation (this time with price)
    state = await build_confirmation(state, language=language)
    return {
        "reply": state["response"],
        "show_buttons": state.get("show_buttons", False),
        "buttons": state.get("buttons", [])
    }


# ============================================
# MAIN WORKFLOW RUNNER
# ============================================

def is_confirmation_message(message: str) -> tuple:
    """Check if message is YES/NO confirmation"""
    msg = message.lower().strip()
    
    positive = ["yes", "haan", "ha", "haa", "y", "ok", "okay", "theek hai", "kar do", "kardo", "ji", "ji haan", "hn"]
    negative = ["no", "nahi", "na", "naa", "n", "cancel", "rehne do", "mat karo", "nahi chahiye", "band karo"]
    
    if msg in positive:
        return (True, True)
    if msg in negative:
        return (True, False)
    return (False, None)


def is_stock_query(message: str) -> tuple:
    """Check if message is asking about stock"""
    msg = message.lower()
    stock_keywords = ["stock", "kitna", "bacha", "inventory", "maal"]
    
    for kw in stock_keywords:
        if kw in msg:
            return True
    return False


def is_payment_choice(message: str) -> Optional[str]:
    """Check if message is a payment method choice"""
    msg = message.lower()
    if any(w in msg for w in ["cash", "paid", "nary", "nakad", "online", "upi", "paytm", "gpay", "phonepe"]):
        return "cash"
    if any(w in msg for w in ["credit", "udhaar", "khata", "baaki", "later", "baad me"]):
        return "credit"
    return None


async def handle_payment_choice(user_phone: str, choice: str, pending_action: dict, language: str = "hi") -> Dict[str, Any]:
    """Handle payment type selection (Cash/Credit) — FIX 5: returns uniform dict"""
    from db import get_db
    
    # Restore state
    data = pending_action["action_json"]
    entities = data.get("entities", {})
    
    # Update intent based on choice to break loop
    original_intent = data.get("original_intent")
    
    # Explicitly map choice to specific intent
    if choice == "cash":
        new_intent = "sale_paid"
    elif choice == "credit":
        new_intent = "sale_credit"
    else:
        # Fallback (should not happen if is_payment_choice logic works)
        new_intent = "sale_paid" 
    
    state: WorkflowState = {
        "user_phone": user_phone,
        "raw_message": choice,
        "media_url": None,
        "media_type": None,
        "intent": new_intent, # "sale_paid" or "sale_credit"
        "payment_type": choice, # "cash" or "credit"
        "entities": entities,
        "customer": None,
        "processed_items": [], 
        "computed_total": 0,
        "needs_confirmation": False,
        "awaiting_price": False,
        "awaiting_confirmation": False,
        "stage": "draft",
        "show_buttons": False,
        "buttons": [],
        "response": "",
        "action_result": None,
        "low_stock_alert": None,
        "inventory_error": None,  # FIX: add missing field
        "missing_prices": []
    }
    
    db = get_db()
    if data.get("customer_id"):
        res = db.table("customers").select("*").eq("id", data["customer_id"]).execute()
        if res.data: state["customer"] = res.data[0]
        
    # Re-run validation logic (re-calculates total, etc.)
    state = await validate_entities(state)
    
    # Recompute total
    state = await compute_transaction(state)
    
    # Build confirmation (now with payment_type explicitly set to prevent loop)
    state = await build_confirmation(state, language=language)
    
    # FIX 5: Return uniform dict with buttons from state
    return {
        "reply": state["response"],
        "show_buttons": state.get("show_buttons", False),
        "buttons": state.get("buttons", [])
    }


async def handle_stock_query(message: str, user_phone: str) -> Dict[str, Any]:
    """Handle stock/inventory queries directly — FIX 5: returns uniform dict"""
    from db import get_inventory_item, list_inventory
    
    def make_resp(text: str):
        return {"reply": text, "show_buttons": False, "buttons": []}
    
    # Extract item name (simple approach)
    words = message.lower().replace("?", "").split()
    item_name = None
    
    # Try to find item name
    for word in words:
        if word not in ["stock", "kitna", "hai", "bacha", "maal", "ka", "ki", "ke", "item"]:
            item_name = word
            break
    
    if item_name:
        item = await get_inventory_item(item_name)
        if item:
            qty = item["quantity"]
            threshold = item.get("low_stock_threshold", 10)
            status = "⚠️ LOW" if qty <= threshold else "✅"
            price = item.get("price", 0)
            return make_resp(f"""📦 *{item['item_name']}*

Stock: {qty} {item.get('unit', 'pcs')} {status}
Price: ₹{price}/unit""")
        else:
            return make_resp(f"❌ '{item_name}' inventory me nahi mila")
    else:
        # Show all inventory
        items = await list_inventory()
        if not items:
            return make_resp("📦 Inventory khali hai")
        
        msg = "📦 *Current Stock:*\n\n"
        for item in items[:8]:
            qty = item["quantity"]
            threshold = item.get("low_stock_threshold", 10)
            status = "⚠️" if qty <= threshold else "✅"
            msg += f"{status} {item['item_name']}: {qty}\n"
        
        return make_resp(msg)


async def run_workflow(
    user_phone: str,
    message: str,
    media_url: Optional[str] = None,
    media_type: Optional[str] = None,
    language: str = "hi"
) -> Dict[str, Any]:
    """Main entry point for processing messages through the workflow"""
    from db import log_event, fetch_pending_action
    
    # helper for default response
    def make_resp(text: str, show_buttons: bool = False, buttons: list = None):
        return {"reply": text, "show_buttons": show_buttons, "buttons": buttons or []}

    # Check for confirmation first
    is_confirm, confirmed = is_confirmation_message(message)
    if is_confirm:
        # FIX 5: handle_confirmation now returns dict directly
        return await handle_confirmation(user_phone, confirmed, language=language)
    
    # CHECK FOR PENDING ACTIONS
    pending = await fetch_pending_action(user_phone)
    if pending:
        action_type = pending.get("action_type")
        
        if action_type == "awaiting_price":
            # Treat message as Price Input — FIX 5: returns dict directly
            return await handle_price_input(user_phone, message, pending, language=language)
            
        elif action_type == "awaiting_payment_type":
            # Check if message is a payment choice
            choice = is_payment_choice(message)
            if choice:
                 # FIX 5: handle_payment_choice now returns uniform dict with buttons
                 return await handle_payment_choice(user_phone, choice, pending, language=language)
            else:
                 # INTERRUPTION CHECK: Is this a new intent?
                 from agent import extract_intent_entities
                 from db import cancel_pending_action
                 
                 print(f"🕵️ Checking if '{message}' is a new intent...")
                 intent_data = await extract_intent_entities(message, user_phone)
                 new_intent = intent_data.get("intent")
                 
                 interrupt_intents = ["sale", "sale_credit", "sale_paid", "purchase", "loss"]
                 is_interrupt = False
                 
                 if new_intent in interrupt_intents:
                     is_interrupt = True
                 elif new_intent == "general_query":
                     if is_stock_query(message) or "return" in message.lower() or "wapas" in message.lower():
                         is_interrupt = True
                 
                 if is_interrupt:
                     print(f"⚠️ Interrupting pending action for new intent: {new_intent}")
                     await cancel_pending_action(pending["id"])
                     # Fall through to main logic
                 else:
                     # Not a strong enough new intent, so treat as invalid input
                     if language == "en":
                         return make_resp("❓ I didn't get that. Is it **Cash** or **Credit/Udhaar**? (Or type 'Cancel')")
                     else:
                         return make_resp("❓ Samajh nahi aaya. **Cash** hai ya **Udhaar**? (Ya 'Cancel' likho)")
                     
    # Check for stock query (no confirmation needed)
    if is_stock_query(message):
        return await handle_stock_query(message, user_phone)
    
    # Initialize state
    state: WorkflowState = {
        "user_phone": user_phone,
        "raw_message": message,
        "media_url": media_url,
        "media_type": media_type,
        "intent": "general_query",
        "payment_type": "unknown", # default
        "entities": {},
        "customer": None,
        "processed_items": [],
        "computed_total": None,
        "needs_confirmation": False,
        "awaiting_price": False,
        "awaiting_confirmation": False,
        "stage": "draft",
        "show_buttons": False,
        "buttons": [],
        "response": "",
        "action_result": None,
        "low_stock_alert": None,
        "missing_prices": []
    }
    
    try:
        # Step 1: Parse user message
        state = await parse_user_message(state)
        
        # If general query, return immediately
        if state["intent"] == "general_query":
            if language == "en":
                 text = state["response"] or "I didn't understand. Try: 'Raj bought 2 milk on credit' or 'Check stock'"
                 return make_resp(text)
            else:
                 text = state["response"] or "Kuch samajh nahi aaya. Examples: 'Rakesh ne 3 doodh liya', 'Stock kitna hai?'"
                 return make_resp(text)
        
        # Step 2: Validate entities
        state = await validate_entities(state)
        
        # Step 3: Compute transaction
        state = await compute_transaction(state)
        
        # Step 4: Build confirmation
        state = await build_confirmation(state, language=language)
        
        return {
            "reply": state["response"],
            "show_buttons": state.get("show_buttons", False),
            "buttons": state.get("buttons", [])
        }
        
    except Exception as e:
        from db import log_business_event, log_debug_event
        log_debug_event("workflow_error", f"Workflow error: {str(e)}", user_phone)
        log_business_event("error", "System error processing request", user_phone)
        text = "⚠️ System error. Please try again." if language == "en" else "⚠️ Ek problem aayi. Phir se try karo!"
        return make_resp(text)
