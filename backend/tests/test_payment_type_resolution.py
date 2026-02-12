import pytest
import asyncio
from httpx import AsyncClient
import uuid

@pytest.mark.asyncio
async def test_payment_type_resolution_loop():
    """
    Test regression: Agent asks Payment Type -> User says "cash" -> Agent asks AGAIN (Loop).
    Fix: Agent should accept "cash" and move to confirmation.
    """
    async with AsyncClient(base_url="http://localhost:8000", timeout=30.0) as ac:
        user_id = f"test_user_loop_{uuid.uuid4().hex[:6]}"
        item_name = f"LoopItem_{uuid.uuid4().hex[:6]}"
        
        # 1. INIT: "Gaurab took 6 frooti" (Simulated)
        print(f"\n--- Step 1: Init (User: {user_id}) ---")
        # Ensure item has price or provide price to skip price stage?
        # If I use "frooti", it might not have price.
        # "Milk" usually has price?
        # I'll use "Milk" to skip price stage, or provide price.
        # Let's use "Milk" assuming it has price, or if it asks price, I'll provide it.
        # But to be safe, I'll use "Milk 2 packets" which triggered "Payment Type" in previous test (failed assertion but showed "Is it Cash...").
        
        res = await ac.post("/api/chat", json={"user_id": user_id, "message": "Milk 2 packets"})
        data = res.json()
        print(f"Agent Step 1: {data['reply']}")
        
        # If asks for price, give it.
        if "number" in data['reply'] or "price" in data['reply'].lower():
             print("--- Step 1.5: Providing Price ---")
             res = await ac.post("/api/chat", json={"user_id": user_id, "message": "40"})
             data = res.json()
             print(f"Agent Step 1.5: {data['reply']}")

        # Now it should be asking for Payment Type
        assert "Cash" in data['reply'] or "Credit" in data['reply'] or "Udhaar" in data['reply']
        
        # 2. PROVIDE PAYMENT TYPE: "cash"
        print("\n--- Step 2: Provide 'cash' ---")
        res = await ac.post("/api/chat", json={"user_id": user_id, "message": "cash"})
        data = res.json()
        print(f"Agent Step 2: {data['reply']}")
        
        # BUG CHECK: Does it ask again?
        if "Cash" in data['reply'] and "Credit" in data['reply'] and "?" in data['reply']:
            pytest.fail("Regression: Agent is looping (asking for Payment Type again)!")
            
        # Expectation: Confirmation Message or "Recorded" (if I confirm? No, shows buttons)
        # Should show buttons or Total
        assert "Total" in data['reply'] or "Confirm" in data['reply'] or data['show_buttons'] is True

if __name__ == "__main__":
    asyncio.run(test_payment_type_resolution_loop())
