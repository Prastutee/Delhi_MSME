import asyncio
import sys
import os
import httpx
import time
import uuid

# Add parent directory to path to import backend modules if needed, 
# but we will primarily test via API to simulate real traffic.
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

BASE_URL = "http://localhost:8000"

async def test_concurrent_inventory_updates():
    """
    Test 1: Concurrent Inventory Updates
    Simulate multiple identical requests to buy the same item at the same time.
    Expected: Inventory should decrement correctly, or some requests might fail if locking works (though inventory updates in db.py are atomic-ish).
    
    Actually, my fix in db.py was 'atomic-like' for the dashboard, but the Agent uses `graph.py` which now has `confirm_pending_action` locking.
    
    Let's test the Agent Flow concurrency:
    1. Create a pending action (e.g. Sale of 1 Milk).
    2. Send TWO "YES" confirmations simultaneously.
    3. Only ONE should succeed. The other should fail with "Already processed".
    """
    print("\n--- TEST 1: Atomic Locking on Confirmation ---")
    
    # 1. Setup: Create a pending action
    # We can't easily inject a pending action via API without a full flow, 
    # so we might need to use the DB function directly or mock it.
    # Let's use internal DB functions for setup to ensure we have a valid pending action.
    
    from db import store_pending_action, get_db, update_inventory, get_inventory_item
    
    user_phone = f"test_{uuid.uuid4().hex[:8]}"
    item_name = "TestCookie"
    
    # Create test item
    await update_inventory(item_name, 100, "set", user_phone="setup")
    print(f"Set {item_name} stock to 100")
    
    # Create pending action
    action_data = {
        "entities": {"items": [{"name": item_name, "quantity": 1, "total": 10}]},
        "processed_items": [{"name": item_name, "quantity": 1, "total": 10, "unit_price": 10}],
        "computed_total": 10,
        "payment_type": "cash"
    }
    
    pending = await store_pending_action(user_phone, "sale_paid", action_data)
    print(f"Created pending action {pending['id']} for user {user_phone}")
    
    # 2. Attack: Send 2 concurrent 'YES' messages
    # We need to hit the webhook or run_workflow.
    # Since run_workflow is internal, let's call it via a wrapper script or just import it.
    # Importing is easier/faster for verification than spinning up ngrok/webhooks.
    
    from graph import run_workflow
    
    print("Launching 2 concurrent confirmation attempts...")
    
    async def confirm_task(name):
        return await run_workflow(user_phone, "YES", language="en")
        
    responses = await asyncio.gather(
        confirm_task("A"),
        confirm_task("B")
    )
    
    # 3. Analyze
    success_count = 0
    fail_count = 0
    
    for r in responses:
        reply = r["reply"]
        print(f"Response: {reply[:50]}...")
        if "Cash Sale Recorded" in reply or "Receipt" in reply:
            success_count += 1
        elif "already been processed" in reply or "No pending action found" in reply:
            fail_count += 1
        else:
            print(f"Unexpected response: {reply}")
            
    print(f"\nResult: Success={success_count}, Blocked={fail_count}")
    
    if success_count == 1 and fail_count == 1:
        print("[PASS] Atomic locking prevented double-submission.")
    else:
        print(f"[FAIL] Atomic locking failed. Success={success_count}, Blocked={fail_count}")
        sys.exit(1)
        
    # Check inventory
    item = await get_inventory_item(item_name)
    print(f"Final Stock: {item['quantity']} (Expected 99)")
    
    if item['quantity'] == 99:
        print("[PASS] Inventory decremented exactly once.")
    else:
        print("[FAIL] Inventory miscount.")
        sys.exit(1)

async def main():
    try:
        await test_concurrent_inventory_updates()
    except Exception as e:
        print(f"Test failed with error: {e}")
        sys.exit(1)

if __name__ == "__main__":
    asyncio.run(main())
