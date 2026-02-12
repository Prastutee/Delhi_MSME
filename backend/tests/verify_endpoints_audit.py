import requests
import sys

BASE_URL = "http://localhost:8000"

ENDPOINTS = [
    ("GET", "/api/stats"),
    ("GET", "/api/customers"),
    ("GET", "/api/inventory"),
    ("GET", "/api/transactions"),
    ("GET", "/api/reminders"),
    ("GET", "/api/logs?limit=5"),
]

def test_endpoints():
    print("🔍 VERIFYING BACKEND ENDPOINTS...\n")
    failed = 0
    
    for method, path in ENDPOINTS:
        url = f"{BASE_URL}{path}"
        try:
            if method == "GET":
                response = requests.get(url)
            
            status = response.status_code
            if status == 200:
                print(f"✅ {method} {path} - OK")
            else:
                print(f"❌ {method} {path} - FAILED ({status})")
                print(f"   Response: {response.text[:200]}")
                failed += 1
        except Exception as e:
            print(f"❌ {method} {path} - EXCEPTION: {e}")
            failed += 1

    # Test Chat specially
    print("\n💬 TESTING CHAT API...")
    try:
        chat_res = requests.post(
            f"{BASE_URL}/api/chat",
            json={"user_id": "audit_user", "message": "Test Message"}
        )
        if chat_res.status_code == 200:
            print(f"✅ POST /api/chat - OK")
        else:
            print(f"❌ POST /api/chat - FAILED ({chat_res.status_code})")
            print(f"   Response: {chat_res.text[:200]}")
            failed += 1
    except Exception as e:
        print(f"❌ POST /api/chat - EXCEPTION: {e}")
        failed += 1

    print(f"\n{'='*30}")
    if failed == 0:
        print("✅ ALL ENDPOINTS OPERATIONAL")
        sys.exit(0)
    else:
        print(f"❌ {failed} ENDPOINTS FAILED")
        sys.exit(1)

if __name__ == "__main__":
    test_endpoints()
