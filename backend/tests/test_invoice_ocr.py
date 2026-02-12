"""
Invoice OCR Quality Test
Verifies:
1. Preprocessing runs without error on valid image.
2. OCR.Space response (mocked) with invoice table is extracted.
3. Agent extracts items from the invoice text.
"""
import pytest
import sys
import os
import io
import json
from unittest.mock import patch, AsyncMock, MagicMock
from PIL import Image

# Add backend to path
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from tools.ocr import extract_text_ocr_space
from graph import run_workflow
import agent

# Sample Invoice Text from OCR
INVOICE_TEXT = """INVOICE #1023
Date: 2023-10-27
Vendor: Sharma Distributors

Item          Qty    Price    Total
Milk Amul 1L   10     60.00    600.00
Bread          5      40.00    200.00
Eggs (Tray)    2      150.00   300.00

Total: 1100.00"""

def create_dummy_image():
    """Create a valid 100x100 JPEG image bytes"""
    img = Image.new('RGB', (100, 100), color = 'red')
    buf = io.BytesIO()
    img.save(buf, format='JPEG')
    return buf.getvalue()

class MockResponse:
    def __init__(self, json_data, status_code=200):
        self._json = json_data
        self.status_code = status_code
        self.text = "Mock Body"
    def json(self):
        return self._json

@pytest.mark.asyncio
async def test_invoice_ocr_pipeline():
    print("\nTEST: Invoice OCR Pipeline")
    
    # Mock OCR.Space Response
    mock_response_data = {
        "ParsedResults": [
            {
                "ParsedText": INVOICE_TEXT,
                "ErrorMessage": "",
                "ErrorDetails": ""
            }
        ],
        "OCRExitCode": 1,
        "IsErroredOnProcessing": False
    }
    
    # Mock DB functions used by agent
    with patch("httpx.AsyncClient") as MockClient, \
         patch("db.get_inventory_item", new_callable=AsyncMock) as mock_get_item, \
         patch("db.store_pending_action", new_callable=AsyncMock) as mock_store, \
         patch("db.find_customer_by_name", new_callable=AsyncMock) as mock_find_cust, \
         patch("db.get_or_create_customer", new_callable=AsyncMock) as mock_create_cust, \
         patch("agent.call_gemini", new_callable=AsyncMock) as mock_gemini:
         
         # Setup Mock HTTP Client
        mock_active_client = AsyncMock()
        mock_active_client.post.return_value = MockResponse(mock_response_data)
        
        # Configure Async Context Manager
        MockClient.return_value.__aenter__ = AsyncMock(return_value=mock_active_client)
        MockClient.return_value.__aexit__ = AsyncMock(return_value=None)
        
        # Setup Mock DB
        # Dynamic item lookup
        def get_item_side_effect(name):
            if "Milk" in name: return {"item_name": "Milk Amul 1L", "price": 60, "quantity": 100}
            if "Bread" in name: return {"item_name": "Bread", "price": 40, "quantity": 50}
            if "Eggs" in name: return {"item_name": "Eggs (Tray)", "price": 150, "quantity": 20}
            return None
        mock_get_item.side_effect = get_item_side_effect
        mock_find_cust.return_value = {"id": "cust_123", "name": "Sharma Distributors"}
        mock_create_cust.return_value = {"id": "cust_new", "name": "New Customer", "phone": "9876543210"}

        # Mock LLM Response for Invoice
        mock_llm_json = json.dumps({
            "intent": "sale_paid",
            "entities": {
                "items": [
                    {"name": "Milk", "quantity": 10},
                    {"name": "Bread", "quantity": 5}
                ]
            },
            "response": "Added Milk and Bread",
            "needs_confirmation": True
        })
        mock_gemini.return_value = mock_llm_json

        # 1. Run Extract Text (Trigger Preprocessing + OCR Mock)
        image_bytes = create_dummy_image()
        extracted_text = await extract_text_ocr_space(image_bytes)
        
        # Provide helpful debug if this fails
        if INVOICE_TEXT not in extracted_text:
            print(f"FAILURE: Extracted text was:\n{extracted_text}")
        
        assert INVOICE_TEXT in extracted_text
        print("   [OK] Text Extraction & Preprocessing (Simulated) Success")
        
        # 2. Run Agent Workflow with Extracted Text
        response = await run_workflow(extracted_text, "9876543210")
        
        # 3. Verify Response contains items
        print(f"   [INFO] Agent Response: {response}")
        
        assert "Milk" in response
        assert "10" in response
        assert "Bread" in response
        assert "5" in response
        
        print("   [OK] Agent parsed invoice items successfully")

if __name__ == "__main__":
    import asyncio
    asyncio.run(test_invoice_ocr_pipeline())
