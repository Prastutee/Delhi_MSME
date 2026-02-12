import pytest
import asyncio
from httpx import AsyncClient


# Mock DB or dependencies if needed, but integration test is better
# We will use the running server or TestClient

@pytest.mark.asyncio
async def test_master_flow_integration():
    """
    Test the full 5-stage Master Prompt flow:
    1. User: "Milk 2 packets" (Missing Price) -> Agent: "Price?"
    2. User: "40" (Missing Payment Type) -> Agent: "Cash or Credit?"
    3. User: "Udhaar" (Ready) -> Agent: "Confirm?" (Show Buttons)
    4. User: Confirm -> Agent: "Recorded"
    """
    import uuid
    async with AsyncClient(base_url="http://localhost:8000", timeout=30.0) as ac:
        user_id = f"test_user_{uuid.uuid4()}"
        item_name = f"CrypticItem_{uuid.uuid4().hex[:6]}"
        
        # 1. INIT / DRAFT
        print(f"\n--- Step 1: Init (User: {user_id}) ---")
        res = await ac.post("/api/chat", json={"user_id": user_id, "message": f"{item_name} 2 packets"})
        data = res.json()
        print(f"Agent: {data['reply']}")
        assert "Price" in data['reply'] or "price" in data['reply']
        assert data['show_buttons'] is False
        
        # 2. PROVIDE PRICE
        print("\n--- Step 2: Price ---")
        res = await ac.post("/api/chat", json={"user_id": user_id, "message": "40"})
        data = res.json()
        print(f"Agent: {data['reply']}")
        assert "Cash" in data['reply'] or "Udhaar" in data['reply']
        assert data['show_buttons'] is False  # Still asking for payment type
        
        # 3. PROVIDE PAYMENT TYPE
        print("\n--- Step 3: Payment Type ---")
        res = await ac.post("/api/chat", json={"user_id": user_id, "message": "Udhaar"})
        data = res.json()
        print(f"Agent: {data['reply']}")
        assert "Total" in data['reply']
        assert data['show_buttons'] is True
        assert len(data['buttons']) > 0
        
        # 4. CONFIRM
        print("\n--- Step 4: Confirm ---")
        res = await ac.post("/api/confirm", json={"user_id": user_id, "confirmed": True})
        data = res.json()
        print(f"Agent: {data['reply']}")
        assert "Recorded" in data['reply'] or "Udhaar" in data['reply']

if __name__ == "__main__":
    # Manually run async test if executed as script
    asyncio.run(test_master_flow_integration())
