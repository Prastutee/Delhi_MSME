import requests

BASE_URL = "http://localhost:8000"

def test_stt_point():
    print("🎤 VERIFYING STT ENDPOINT WIRING...")
    
    # Test 1: Missing File
    print("\n1. Testing Missing File (Expect 422)...")
    try:
        res = requests.post(f"{BASE_URL}/api/stt")
        if res.status_code == 422:
            print("   ✅ Correctly rejected missing file (422)")
        else:
            print(f"   ❌ Unexpected status: {res.status_code}")
    except Exception as e:
        print(f"   ❌ Connection failed: {e}")

    # Test 2: Invalid File Content (Expect 500 or Error from Groq)
    # We send a text file disguised as audio. Groq should reject it or code should catch it.
    print("\n2. Testing Invalid Audio File (Expect 500/Error)...")
    try:
        files = {'file': ('test.txt', b'This is not audio', 'text/plain')}
        res = requests.post(f"{BASE_URL}/api/stt", files=files)
        
        print(f"   Status: {res.status_code}")
        print(f"   Response: {res.text}")
        
        if res.status_code == 500 or "Groq" in res.text or "error" in res.text.lower():
             print("   ✅ Correctly attempted processing (and failed as expected on invalid data)")
        else:
             print(f"   ⚠️ Unexpected success/behavior (maybe mock mode?): {res.text}")
             
    except Exception as e:
        print(f"   ❌ Connection failed: {e}")

if __name__ == "__main__":
    test_stt_point()
