import requests
import json
import sys

BASE_URL = "http://localhost:8000"

def test_live_ocr():
    print("🚀 Starting Live Verification...")
    
    # 1. Scan Receipt
    try:
        files = {'file': open('sample_receipt.jpg', 'rb')}
        print("   📸 Sending OCR request...")
        res = requests.post(f"{BASE_URL}/api/ocr", files=files)
        
        if res.status_code != 200:
            print(f"   ❌ Scan Failed: {res.status_code} {res.text}")
            sys.exit(1)
            
        data = res.json()
        if not data.get("success"):
            print(f"   ❌ API Success False: {data}")
            sys.exit(1)
            
        draft = data["draft"]
        print(f"   ✅ Scan Success! Items: {len(draft['items'])}")
        print(f"   📝 Draft: {json.dumps(draft, indent=2)}")
        
        if not draft['items']:
            print(f"   ⚠️ WARNING: No items found. Raw Text:\n{data.get('raw_text', '')}")
            # Do NOT exit, try confirming anyway to test flow (it will fail 400, but we see the error)
            
        # 2. Confirm Purchase
        print("\n   📦 Confirming Purchase...")
        confirm_res = requests.post(f"{BASE_URL}/api/ocr/confirm", json=draft)
        
        if confirm_res.status_code != 200:
            print(f"   ❌ Confirm Failed: {confirm_res.status_code} {confirm_res.text}")
            sys.exit(1)
            
        confirm_data = confirm_res.json()
        print(f"   ✅ Purchase Confirmed! {confirm_data['message']}")
        print("🎉 LIVE CHECK PASSED")
        
    except Exception as e:
        print(f"   ❌ Exception: {e}")
        sys.exit(1)

if __name__ == "__main__":
    test_live_ocr()
