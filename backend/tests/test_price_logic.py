import asyncio
import sys
import os
import pytest
from datetime import datetime

from db import get_db, update_inventory
from graph import run_workflow

TEST_PHONE = "test_price_logic_user"
ITEM_NAME = "logic_test_atta"

@pytest.mark.asyncio
async def test_price_logic():
    print("🧪 TESTING PRICE LOGIC (Unit Price vs Total Amount)...")
    db = get_db()
    
    # 1. Setup: Create item with NO price
    print(f"   Setup: Creating '{ITEM_NAME}' with 0 price...")
    # Update inventory clears/sets items. We want explicit price=0
    # First, ensure it exists
    await update_inventory(ITEM_NAME, 10, "set")
    # Force price to 0/null to trigger "ask for price"
    db.table("inventory").update({"price": None}).eq("item_name", ITEM_NAME).execute()
    
    # 2. Step 1: "Raj ne 2 atta liya"
    print("   User Input 1: 'Raj ne 2 logic_test_atta liya'")
    resp1 = await run_workflow(TEST_PHONE, f"Raj ne 2 {ITEM_NAME} liya", language="en")
    print(f"   Bot Response 1: {resp1}")
    
    # Expectation: Bot asks for price in ENGLISH
    assert "Price needed" in resp1, f"Bot did not ask for price in English. Got: {resp1}"
         
    # 3. Step 2: "40" (Intending 40 per unit)
    print("   User Input 2: '40'")
    resp2 = await run_workflow(TEST_PHONE, "40", language="en")
    print(f"   Bot Response 2: {resp2}")
    
    # Expectation: English Confirmation
    assert "Cash Sale" in resp2, f"Bot did not respond with English Confirmation. Got: {resp2}"
    
    # 4. Verify Pending Action
    # The confirmation message should show the calculated total.
    # We also check the pending_action table to be sure of what's stored.
    pending = db.table("pending_actions").select("*").eq("user_phone", TEST_PHONE).eq("status", "pending").execute()
    
    assert pending.data, "No pending action created after price input."

    data = pending.data[0]["action_json"]
    qty = data.get("quantity", 0)
    unit_price = data.get("unit_price", 0)
    total = data.get("computed_total", 0)
    
    print(f"   📊 CAPTURED STATE:")
    print(f"      Qty: {qty}")
    print(f"      Unit Price: {unit_price}")
    print(f"      Total: {total}")
    
    # CHECK LOGIC
    expected_total = 2 * 40 # 80
    
    if total == 40:
        pytest.fail("❌ BUG CONFIRMED: Total is 40 (Price treated as Total)")
    
    assert total == expected_total, f"Unexpected Total {total}"
    print(f"   ✅ SUCCESS: Total is {total} (2 * 40)")

if __name__ == "__main__":
    asyncio.run(test_price_logic())
