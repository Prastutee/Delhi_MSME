import pytest
import asyncio
from httpx import AsyncClient
import uuid

@pytest.mark.asyncio
async def test_payment_type_no_loop():
    """
    Permanent Regression Test:
    Ensures that once a payment type is provided, the agent DOES NOT ask for it again.
    """
    async with AsyncClient(base_url="http://localhost:8000", timeout=30.0) as ac:
        user_id = f"reg_user_pay_{uuid.uuid4().hex[:6]}"
        item_name = f"RegItem_{uuid.uuid4().hex[:6]}"
        
        # 1. Init with sale intent
        print(f"\n--- Step 1: Init {user_id} ---")
        res = await ac.post("/api/chat", json={"user_id": user_id, "message": f"{item_name} 2 packets"})
        data = res.json()
        print(f"Agent: {data['reply']}")
        
        # If asks for price, provide it
        if "price" in data['reply'].lower() or "number" in data['reply']:
            res = await ac.post("/api/chat", json={"user_id": user_id, "message": "50"})
            data = res.json()
            print(f"Agent (Price): {data['reply']}")
            
        # Should be asking for payment type
        assert "Cash" in data['reply'] or "Credit" in data['reply']
        
        # 2. Provide Payment Type: "cash"
        print("\n--- Step 2: Provide 'cash' ---")
        res = await ac.post("/api/chat", json={"user_id": user_id, "message": "cash"})
        data = res.json()
        print(f"Agent: {data['reply']}")
        
        # 3. VERIFY: Must NOT ask for payment type again
        reply_lower = data['reply'].lower()
        if "cash or credit" in reply_lower or "payment type" in reply_lower:
            pytest.fail("Regression: Agent asked for payment type AGAIN after receiving 'cash'")
            
        # Expectation: Total or Confirm
        assert "Total" in data['reply'] or "Confirm" in data['reply'] or data['show_buttons'] is True

if __name__ == "__main__":
    asyncio.run(test_payment_type_no_loop())
