import requests
import json
import sys

BASE_URL = "http://localhost:8000/api/chat"

def print_step(step, msg):
    print(f"\n🔹 STEP {step}: {msg}")

def chat(message, user_id="dashboard_user"):
    payload = {"user_id": user_id, "message": message}
    try:
        res = requests.post(BASE_URL, json=payload, timeout=30)
        res.raise_for_status()
        data = res.json()
        print(f"   🤖 Bot: {data.get('reply', 'No reply field')}")
        return data.get('reply', '')
    except Exception as e:
        print(f"   ❌ Error: {e}")
        return None

def verify_flow():
    print("🧪 STARTING CHAT FLOW VERIFICATION")
    
    # 1. Initial Request
    print_step(1, "Sending Transaction Request")
    msg = "Rakesh ne 3 doodh udhaar liya"
    print(f"   👤 User: {msg}")
    reply = chat(msg)
    
    if "Confirm" not in reply and "Khata" not in reply:
        print("   ⚠️ Bot did not ask for confirmation clearly.")
    
    # 2. Confirmation
    print_step(2, "Sending Confirmation (YES)")
    print(f"   👤 User: YES")
    reply = chat("YES")
    
    if "Recorded" in reply or "Success" in reply:
        print("   ✅ Transaction appears recorded.")
    else:
        print("   ⚠️ Transaction might not have been recorded.")
        
    print("\n✅ Verification Script Complete")

if __name__ == "__main__":
    verify_flow()
