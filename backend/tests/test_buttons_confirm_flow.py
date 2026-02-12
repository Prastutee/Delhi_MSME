import pytest
import asyncio
from httpx import AsyncClient
import uuid

@pytest.mark.asyncio
async def test_buttons_confirm_flow():
    """
    Permanent Regression Test:
    Ensures that the 'Confirm' button triggers the actual transaction execution.
    Adaptive: follows the agent's prompts rather than assuming a fixed sequence.
    """
    async with AsyncClient(base_url="http://localhost:8000", timeout=30.0) as ac:
        user_id = f"reg_user_btn_{uuid.uuid4().hex[:6]}"
        item_name = "Amul Milk"
        
        # 1. Send initial sale message
        res = await ac.post("/api/chat", json={"user_id": user_id, "message": f"{item_name} 1 packet"})
        data = res.json()
        
        # Adaptive loop: respond to what the agent asks (max 5 iterations)
        for _ in range(5):
            if data.get('show_buttons') is True:
                break  # Reached confirmation stage
            
            reply = data['reply'].lower()
            
            if 'price' in reply or 'number' in reply:
                # Agent asking for price
                res = await ac.post("/api/chat", json={"user_id": user_id, "message": "100"})
                data = res.json()
            elif 'cash' in reply or 'credit' in reply or 'udhaar' in reply or 'payment' in reply:
                # Agent asking for payment type
                res = await ac.post("/api/chat", json={"user_id": user_id, "message": "cash"})
                data = res.json()
            else:
                # Unexpected response — try cash as fallback
                res = await ac.post("/api/chat", json={"user_id": user_id, "message": "cash"})
                data = res.json()
        
        # Check we are at confirmation stage
        assert data['show_buttons'] is True, f"Expected show_buttons=True, got reply: {data['reply'][:200]}"
        assert len(data['buttons']) > 0
        
        # 2. CLICK CONFIRM BUTTON
        print("\n--- Clicking Confirm Button ---")
        res = await ac.post("/api/confirm", json={"user_id": user_id, "confirmed": True})
        data = res.json()
        print(f"Agent: {data['reply']}")
        
        # 3. VERIFY EXECUTION
        assert "Recorded" in data['reply'] or "Sale" in data['reply'] or "✅" in data['reply']
        
        # Verify show_buttons is now False (transaction done)
        assert data.get('show_buttons', False) is False

if __name__ == "__main__":
    asyncio.run(test_buttons_confirm_flow())
