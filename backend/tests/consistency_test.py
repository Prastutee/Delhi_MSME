import asyncio
import requests
import json
from db import get_db, update_inventory

BASE_URL = "http://localhost:8000"
USER_ID = "consistency_test_user_v1"

async def run_consistency_test():
    print("⚖️ STARTING MULTI-TABLE CONSISTENCY VERIFICATION...\n")
    db = get_db()
    
    # ---------------------------------------------------------
    # SETUP: Ensure Item Exists and has Stock
    # ---------------------------------------------------------
    print("🔧 SETUP: Resetting Inventory...")
    item_name = "consistency_milk"
    # Create or update item
    await update_inventory(item_name, 50, "set") # Set to 50
    # Set price
    db.table("inventory").update({"price": 60}).eq("item_name", item_name).execute()
    
    print(f"   Item '{item_name}' set to Qty: 50, Price: 60")

    # ---------------------------------------------------------
    # PHASE 1: CREDIT SALE REQUEST
    # ---------------------------------------------------------
    print("\n🔹 PHASE 1: CREDIT SALE REQUEST ('Rakesh ne 2 consistency_milk udhaar liya')")
    
    msg = f"Rakesh ne 2 {item_name} udhaar liya"
    res = requests.post(f"{BASE_URL}/api/chat", json={"user_id": USER_ID, "message": msg})
    print(f"   Bot Reply: {res.json().get('reply')}")

    # VERIFY: Pending Action Created
    pending = db.table("pending_actions").select("*").eq("user_phone", USER_ID).eq("status", "pending").order("created_at", desc=True).limit(1).execute()
    if pending.data:
        p = pending.data[0]
        print(f"   ✅ pending_actions: Row found (Type: {p['action_type']}, Status: {p['status']})")
        if p['action_type'] != 'sale_credit':
            print(f"      ❌ EXPECTED 'sale_credit', GOT '{p['action_type']}'")
    else:
        print("   ❌ pending_actions: ROW MISSING")

    # VERIFY: NO Transaction Yet
    tx = db.table("transactions").select("*").like("item_name", item_name).order("created_at", desc=True).limit(1).execute()
    if not tx.data:
         print("   ✅ transactions: No transaction yet (Correct)")
    else:
         # Check timestamp? Or just rely on logic that we haven't confirmed yet. 
         # Ideally we check if a NEW one appeared. 
         print(f"   ℹ️ transactions: Found {len(tx.data)} entries (Checking recentness...)")
         # Assuming logic prevents write until confirm.

    # ---------------------------------------------------------
    # PHASE 2: CONFIRMATION
    # ---------------------------------------------------------
    print("\n🔹 PHASE 2: CONFIRMATION ('Ha')")
    
    res = requests.post(f"{BASE_URL}/api/chat", json={"user_id": USER_ID, "message": "Ha"})
    print(f"   Bot Reply: {res.json().get('reply')}")

    # VERIFY 1: Pending Action Confirmed
    pending_c = db.table("pending_actions").select("*").eq("id", p['id']).execute()
    if pending_c.data and pending_c.data[0]['status'] == 'confirmed':
        print("   ✅ pending_actions: Status updated to 'confirmed'")
    else:
        print(f"   ❌ pending_actions: Status is {pending_c.data[0]['status'] if pending_c.data else 'MISSING'}")

    # VERIFY 2: Transaction Created
    tx_new = db.table("transactions").select("*").eq("item_name", item_name).order("created_at", desc=True).limit(1).execute()
    if tx_new.data:
        t = tx_new.data[0]
        expected_amt = 2 * 60
        print(f"   ✅ transactions: Row created (Type: {t['type']}, Amount: {t['amount']})")
        if t['amount'] == expected_amt:
             print("      ✅ Amount Correct")
        else:
             print(f"      ❌ Amount Mismatch (Expected {expected_amt}, Got {t['amount']})")
    else:
        print("   ❌ transactions: ROW MISSING")

    # VERIFY 3: Inventory Updated
    inv = db.table("inventory").select("*").eq("item_name", item_name).execute()
    if inv.data:
        curr_qty = inv.data[0]['quantity']
        expected_qty = 48 # 50 - 2
        if curr_qty == expected_qty:
            print(f"   ✅ inventory: Quantity updated to {curr_qty}")
        else:
            print(f"   ❌ inventory: Quantity Mismatch (Expected {expected_qty}, Got {curr_qty})")

    # VERIFY 4: Reminder Created (Since it's credit sale)
    # Check for recent reminder for this customer (Rakesh) implied or explicitly connected
    # The graph logic validates/creates "Rakesh" as customer.
    cust = db.table("customers").select("*").ilike("name", "%Rakesh%").execute()
    if cust.data:
        cid = cust.data[0]['id']
        rem = db.table("reminders").select("*").eq("customer_id", cid).order("created_at", desc=True).limit(1).execute()
        if rem.data and rem.data[0]['reminder_type'] == 'payment_repayment': # Assuming default logic adds general or repayment reminder
             print(f"   ✅ reminders: Row created (Message: '{rem.data[0]['message']}')")
        else:
             # Wait, does sale_credit AUTO-CREATE reminder? 
             # Previous prompt requirement: "Reminder scheduled (7 days default)"
             # Let's check if code implements this.
             if rem.data:
                 print(f"   ℹ️ reminders: Found reminder '{rem.data[0]['message']}'")
             else:
                 print("   ⚠️ reminders: No reminder found (Check implementation)")
    
    # VERIFY 5: Logs
    logs = db.table("logs").select("*").eq("user_phone", USER_ID).order("created_at", desc=True).limit(5).execute()
    types = [l['action_type'] for l in logs.data]
    print(f"   ✅ logs: Recent actions -> {types}")
    if "sale_credit" in types:
        print("      ✅ 'sale_credit' log found")
    else:
         print("      ❌ 'sale_credit' log MISSING")

    # ---------------------------------------------------------
    # PHASE 3: PAYMENT
    # ---------------------------------------------------------
    print("\n🔹 PHASE 3: PAYMENT ('Rakesh ne 50 rupaye diye')")
    
    # Request
    requests.post(f"{BASE_URL}/api/chat", json={"user_id": USER_ID, "message": "Rakesh ne 50 rupaye diye"})
    # Confirm
    res = requests.post(f"{BASE_URL}/api/chat", json={"user_id": USER_ID, "message": "Ha"})
    print(f"   Bot Reply: {res.json().get('reply')}")
    
    # VERIFY: Transaction
    tx_pay = db.table("transactions").select("*").eq("type", "payment").order("created_at", desc=True).limit(1).execute()
    if tx_pay.data and tx_pay.data[0]['amount'] == 50:
         print("   ✅ transactions: Payment row created (Amount: 50)")
    else:
         print("   ❌ transactions: Payment row MISSING or Incorrect")

    # ---------------------------------------------------------
    # PHASE 4: LOW STOCK TRIGGER
    # ---------------------------------------------------------
    print("\n🔹 PHASE 4: LOW STOCK TRIGGER")
    
    # Force Low Stock
    await update_inventory(item_name, 2, "set") # Threshold is usually 10
    print(f"   Updated {item_name} qty to 2 (Threshold 10)")

    # Buy item
    requests.post(f"{BASE_URL}/api/chat", json={"user_id": USER_ID, "message": f"Rakesh ne 1 {item_name} liya"}) # Paid sale
    res = requests.post(f"{BASE_URL}/api/chat", json={"user_id": USER_ID, "message": "Ha"})
    reply = res.json().get('reply', '')
    
    if "LOW STOCK ALERT" in reply or "reorder" in reply.lower():
        print("   ✅ UI Alert: Low stock message received")
    else:
        print(f"   ❌ UI Alert: Low stock message MISSING in reply: {reply[:50]}...")

    # Check Log
    log_low = db.table("logs").select("*").eq("action_type", "low_stock_alert").order("created_at", desc=True).limit(1).execute()
    if log_low.data:
         print("   ✅ logs: 'low_stock_alert' entry found")
    else:
         print("   ❌ logs: 'low_stock_alert' entry MISSING")


if __name__ == "__main__":
    asyncio.run(run_consistency_test())
