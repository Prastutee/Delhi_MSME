import asyncio
import json
import requests
from db import get_db

async def verify_chat_action():
    print("🧪 STARTING CHAT TRUTH TEST (MULTI-TURN)...")
    db = get_db()
    BASE_URL = "http://localhost:8000"
    USER_ID = "truth_test_user_v2" # New user to ensure clean state
    
    # --- TURN 1: INTENT ---
    print(f"\n   1. Sending 'Rakesh ne 2 doodh udhaar liya' as {USER_ID}...")
    try:
        res1 = requests.post(f"{BASE_URL}/api/chat", json={
            "user_id": USER_ID,
            "message": "Rakesh ne 2 doodh udhaar liya"
        })
        reply1 = res1.json().get("reply", "")
        print(f"      🤖 Reply 1: {reply1}")
    except Exception as e:
        print(f"      ❌ Chat Request 1 Failed: {e}")
        return

    # --- TURN 2: CONFIRMATION ---
    print(f"\n   2. Sending 'Ha' (Confirmation)...")
    try:
        res2 = requests.post(f"{BASE_URL}/api/chat", json={
            "user_id": USER_ID,
            "message": "Ha"
        })
        reply2 = res2.json().get("reply", "")
        print(f"      🤖 Reply 2: {reply2}")
    except Exception as e:
        print(f"      ❌ Chat Request 2 Failed: {e}")
        return

    # --- VERIFICATION ---
    print("\n   3. Verifying DB Persistence...")
    
    # Transaction
    txs = db.table("transactions").select("*").eq("type", "sale_credit").order("created_at", desc=True).limit(1).execute()
    if txs.data:
        tx = txs.data[0]
        # We expect Rakesh, amount ~120 (60x2 from previous logic, or whatever model decided)
        print(f"      ✅ Transaction Found: {tx['description']} - ₹{tx['amount']}")
    else:
        print(f"      ❌ NO Transaction Found! (Checks failed)")

    # Reminder
    rems = db.table("reminders").select("*").eq("status", "pending").order("created_at", desc=True).limit(1).execute()
    if rems.data:
        rem = rems.data[0]
        print(f"      ✅ Reminder Found: {rem['message']} (Next run: {rem['next_run']})")
    else:
        print(f"      ❌ NO Reminder Found!")

    # Logs
    print("\n   4. Verifying Activity Log (Strict Filter)...")
    logs = db.table("logs").select("*").order("created_at", desc=True).limit(5).execute()
    if logs.data:
        print(f"      Found {len(logs.data)} recent logs:")
        ALLOWED = ["sale_credit", "sale_paid", "payment", "reminder_created", "reminder_sent", "inventory_update", "low_stock_alert"]
        for l in logs.data:
            icon = "✅" if l['action_type'] in ALLOWED else "⚠️INVALID"
            print(f"         {icon} [{l['action_type']}] {l['message']}")
    else:
        print(f"      ❌ NO Business Logs Found!")

if __name__ == "__main__":
    asyncio.run(verify_chat_action())
