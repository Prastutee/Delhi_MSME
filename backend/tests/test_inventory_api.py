import pytest
import asyncio
from httpx import AsyncClient, ASGITransport
from main import app
from db import get_db, update_inventory

@pytest.mark.asyncio
async def test_inventory_update_api():
    """
    Test the inventory update endpoint to ensure no regression.
    Specifically tests the fix for the shadowed function name bug.
    """
    print("\n🧪 TESTING INVENTORY UPDATE API...")
    
    # 1. Setup: Create a test item
    item_name = "api_test_item"
    await update_inventory(item_name, 10, "set")
    
    # Get ID
    db = get_db()
    item = db.table("inventory").select("*").eq("item_name", item_name).single().execute()
    item_id = item.data["id"]
    
    # 2. Call API to update quantity
    # Payload matches InventoryUpdate model
    payload = {
        "quantity_change": 5,
        "price": 100.0
    }
    
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        print(f"   Sending request to /api/inventory/update/{item_id}")
        response = await client.post(f"/api/inventory/update/{item_id}", json=payload)
        
    print(f"   Response Status: {response.status_code}")
    print(f"   Response Body: {response.text}")
    
    # 3. Verify
    assert response.status_code == 200, f"API failed with {response.status_code}: {response.text}"
    
    data = response.json()
    assert data["success"] is True
    
    # Verify DB update
    updated_item = db.table("inventory").select("*").eq("id", item_id).single().execute()
    new_qty = updated_item.data["quantity"]
    new_price = updated_item.data["price"]
    
    # Expected: 10 + 5 = 15
    assert new_qty == 15, f"Quantity mismatch. Expected 15, got {new_qty}"
    assert new_price == 100.0, f"Price mismatch. Expected 100.0, got {new_price}"
    
    print("   ✅ Inventory Update API Success")
