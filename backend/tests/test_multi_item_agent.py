import pytest
import sys
import os
from unittest.mock import patch, AsyncMock

# Add backend to path
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from graph import run_workflow
import db # Import db to ensure it is loaded for patching

# Mock Data
MULTI_ITEM_INTENT = {
    "intent": "sale_paid",
    "entities": {
        "customer_name": "Rakesh",
        "items": [
            {"name": "Milk", "quantity": 10, "price": 30},
            {"name": "Bread", "quantity": 5, "price": 40}
        ],
        "amount": 0
    },
    "needs_confirmation": True,
    "response": "Confirm sale?"
}

SINGLE_ITEM_INTENT = {
    "intent": "purchase",
    "entities": {
        "items": [{"name": "Rice", "quantity": 50}],
        "amount": 0
    },
    "needs_confirmation": True,
    "response": "Confirm purchase?"  
}

@pytest.mark.asyncio
async def test_multi_item_flow():
    """Test processing of multiple items in one message"""
    print("\n🧪 TEST: Multi-Item Workflow")
    
    with patch("agent.extract_intent_entities", new_callable=AsyncMock) as mock_extract, \
         patch("db.store_pending_action", new_callable=AsyncMock) as mock_store, \
         patch("db.get_inventory_item", new_callable=AsyncMock) as mock_get_item, \
         patch("db.find_customer_by_name", new_callable=AsyncMock) as mock_find_customer, \
         patch("db.get_or_create_customer", new_callable=AsyncMock) as mock_create_customer:
         
        mock_extract.return_value = MULTI_ITEM_INTENT
        
        def get_item_side_effect(name):
            if "Milk" in name: return {"item_name": "Milk", "price": 30, "quantity": 100}
            if "Bread" in name: return {"item_name": "Bread", "price": 40, "quantity": 100}
            return None
            
        mock_get_item.side_effect = get_item_side_effect
        
        # 1. Run Workflow
        response = await run_workflow("Rakesh ne 10 milk aur 5 bread liye", "9876543210")
        
        # Verify response contains both items
        assert "Milk" in response
        assert "10" in response
        assert "Bread" in response
        assert "5" in response
        assert "Total" in response
        
        # Verify pending action stored with processed_items
        mock_store.assert_called_once()
        call_args = mock_store.call_args[1]
        action_data = call_args["action_data"]
        
        assert "processed_items" in action_data
        items = action_data["processed_items"]
        assert len(items) == 2
        # Note: Name might be "Milk" from DB or raw
        
        print("   ✅ Multi-item state processed correctly")

@pytest.mark.asyncio
async def test_ocr_text_flow():
    """Test workflow with OCR-style text input (newline separated)"""
    print("\n🧪 TEST: OCR Text Workflow")
    
    ocr_intent = {
        "intent": "sale_paid",
        "entities": {
            "items": [
                {"name": "Item A", "quantity": 1, "price": 100},
                {"name": "Item B", "quantity": 2, "price": 50}
            ],
            "amount": 0
        },
        "needs_confirmation": True,
        "response": "Confirm?"
    }
    
    with patch("agent.extract_intent_entities", new_callable=AsyncMock) as mock_extract, \
         patch("db.store_pending_action", new_callable=AsyncMock) as mock_store, \
         patch("db.get_inventory_item", new_callable=AsyncMock) as mock_get_item:
         
        mock_extract.return_value = ocr_intent
        mock_get_item.return_value = None # Item not in DB, use raw
        
        response = await run_workflow("Item A 100\nItem B 50", "9876543210")
        
        assert "Item A" in response
        assert "Item B" in response
        assert "Total" in response
        print("   ✅ OCR text handled correctly")

if __name__ == "__main__":
    import asyncio
    asyncio.run(test_multi_item_flow())
    asyncio.run(test_ocr_text_flow())
