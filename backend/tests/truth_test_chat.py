import asyncio
import json
from db import get_db

async def verify_chat_action():
    print("🧪 STARTING CHAT TRUTH TEST...")
    db = get_db()
    
    # 1. Simulate Chat Input (We can't simulate LLM easily here without calling API, 
    # but we can simulate the RESULT of the LLM -> Backend processing i.e. record sale)
    # Actually, User wants FULL END-TO-END. So we must call the endpoint.
    
    import requests
    BASE_URL = "http://localhost:8000"
    
    # Step 1: Send Message
    print("   1. Sending 'Rakesh ne 2 doodh udhaar liya'...")
    try:
        res = requests.post(f"{BASE_URL}/api/chat", json={
            "user_id": "truth_test_user",
            "message": "Rakesh ne 2 doodh udhaar liya"
        })
        print(f"      Response: {res.status_code}")
        print(f"      Body: {res.json()}")
    except Exception as e:
        print(f"      ❌ Chat Request Failed: {e}")
        return

    # User requirement: "Ask confirmation -> On confirm -> Insert"
    # Current implementation might be direct or require confirmation. 
    # Let's see what the response says. If it asks for confirmation, we confirm.
    
    # Check DB for Transaction
    print("\n   2. Verifying Transaction in DB...")
    txs = db.table("transactions").select("*").order("created_at", desc=True).limit(1).execute()
    if txs.data:
        tx = txs.data[0]
        print(f"      ✅ Transaction Found: {tx['description']} - ₹{tx['amount']}")
    else:
        print(f"      ❌ NO Transaction Found! (Chat failed to persist)")

    # Check DB for Reminder
    print("\n   3. Verifying Reminder in DB...")
    rems = db.table("reminders").select("*").order("created_at", desc=True).limit(1).execute()
    if rems.data:
        rem = rems.data[0]
        print(f"      ✅ Reminder Found: {rem['message']} (Status: {rem['status']})")
    else:
        print(f"      ❌ NO Reminder Found!")

    # Check DB for Activity Log
    print("\n   4. Verifying Activity Log in DB...")
    logs = db.table("logs").select("*").order("created_at", desc=True).limit(5).execute()
    if logs.data:
        print(f"      ✅ Logs Found: {len(logs.data)} recent entries")
        for l in logs.data:
            print(f"         - [{l['action_type']}] {l['message']}")
            
            # Strict Filter Check
            ALLOWED = ["sale_credit", "sale_paid", "payment", "reminder_created", "reminder_sent", "inventory_update", "low_stock_alert"]
            if l['action_type'] not in ALLOWED:
                 print(f"         ⚠️ INVALID LOG TYPE FOUND: {l['action_type']}")
    else:
        print(f"      ❌ NO Business Logs Found!")

if __name__ == "__main__":
    asyncio.run(verify_chat_action())
