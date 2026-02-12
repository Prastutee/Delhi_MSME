import asyncio
import json
import requests
from db import get_db

async def verify_button_actions():
    print("🧪 STARTING BUTTON ACTION TRUTH TEST...")
    db = get_db()
    BASE_URL = "http://localhost:8000"
    
    # --- TEST 1: CREATE REMINDER BUTTON ---
    print("\n   1. Simulating 'Create Reminder' Button Click...")
    try:
        res = requests.post(f"{BASE_URL}/api/reminders", json={
            "customer_id": "demo_customer_123", # Assuming this ID exists or we might fail FK, let's use a safe one or create one
            # Actually, let's just use a dummy ID and strict schema might fail if foreign key constraint exists. 
            # We should probably fetch a real customer first.
            "message": "Test Reminder Button",
            "repeat_interval_days": 7
        })
        
        # If 500/FK error, fetch a real customer first
        if res.status_code != 200:
             # Fetch customer
             c_res = requests.get(f"{BASE_URL}/api/customers")
             custs = c_res.json().get("customers", [])
             if custs:
                 cid = custs[0]["id"]
                 # Retry
                 res = requests.post(f"{BASE_URL}/api/reminders", json={
                    "customer_id": cid,
                    "message": "Test Reminder Button",
                    "repeat_interval_days": 7
                })

        print(f"      API Response: {res.status_code}")
        
        # DB Verification
        rem = db.table("reminders").select("*").eq("message", "Test Reminder Button").execute()
        if rem.data:
             print(f"      ✅ DB Row Created: {rem.data[0]['id']}")
        else:
             print(f"      ❌ DB Row MISSING!")

    except Exception as e:
        print(f"      ❌ Action Failed: {e}")


    # --- TEST 2: ADD INVENTORY BUTTON ---
    print("\n   2. Simulating 'Add Inventory' Button Click...")
    try:
        item_name = f"Test Item {asyncio.get_event_loop().time()}"
        res = requests.post(f"{BASE_URL}/api/inventory/add", json={
            "item_name": item_name,
            "quantity": 50,
            "unit": "pcs",
            "price": 100
        })
        print(f"      API Response: {res.status_code}")
        
        # DB Verification
        inv = db.table("inventory").select("*").eq("item_name", item_name).execute()
        if inv.data:
             print(f"      ✅ DB Row Created: {inv.data[0]['id']} (Qty: {inv.data[0]['quantity']})")
        else:
             print(f"      ❌ DB Row MISSING!")

    except Exception as e:
        print(f"      ❌ Action Failed: {e}")

if __name__ == "__main__":
    asyncio.run(verify_button_actions())
