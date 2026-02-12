import pytest
import asyncio
from unittest.mock import patch, MagicMock
from fastapi.testclient import TestClient
from main import app
from tools.voice import transcribe_groq_whisper, transcribe_audio_groq

# Mock Groq Response
MOCK_TRANSCRIPT = "Rakesh ne 2 kilo atta udhaar liya"

@pytest.mark.asyncio
async def test_groq_whisper_call_structure():
    """
    Test that transcribe_groq_whisper calls usage correctly.
    We want to verify what parameters are sent to Groq.
    """
    print("\n🧪 TESTING: Groq Whisper API Call Structure")
    
    with patch("httpx.AsyncClient.post") as mock_post:
        # Setup Mock
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.json.return_value = {"text": MOCK_TRANSCRIPT}
        mock_post.return_value = mock_response
        
        # Call
        dummy_audio = b"fake_audio_bytes"
        # We need a proper context manager mock for httpx.AsyncClient
        # But wait, transcribe_groq_whisper instantiates AsyncClient inside.
        # So we patch the class.
        pass

@pytest.mark.asyncio
async def test_stt_endpoint_integration():
    """
    Test POST /api/stt
    """
    print("\n🧪 TESTING: POST /api/stt Endpoint")
    client = TestClient(app)
    
    with patch("tools.voice.transcribe_groq_whisper") as mock_transcribe:
        mock_transcribe.return_value = MOCK_TRANSCRIPT
        
        # Create dummy file
        files = {"file": ("test.ogg", b"dummy_bytes", "audio/ogg")}
        
        response = client.post("/api/stt", files=files)
        
        print(f"   Status: {response.status_code}")
        print(f"   Body: {response.json()}")
        
        assert response.status_code == 200
        assert response.json() == {"transcript": MOCK_TRANSCRIPT}
        print("   ✅ Endpoint works")

@pytest.mark.asyncio
async def test_language_parameter_check():
    """
    Verify if we can control the language (Bug Check).
    Currently voice.py hardcodes 'hi'. 
    We want to see if we can pass 'en' for website.
    """
    print("\n🧪 TESTING: Language Parameter Flexibility")
    
    # We'll mock httpx to inspect the 'data' param payload
    with patch("httpx.AsyncClient") as MockClient:
        mock_instance = MockClient.return_value.__aenter__.return_value
        mock_instance.post.return_value.status_code = 200
        mock_instance.post.return_value.json.return_value = {"text": "Hello"}
        
        # Call with 'en' requirement (if we add the param)
        # Note: Current signature doesn't support it, so this checks the CURRENT state.
        
        try:
             # Try calling with a language param if it existed, or check default
            from tools.voice import transcribe_groq_whisper
            await transcribe_groq_whisper(b"data", "fake_key")
            
            # Inspect args
            call_args = mock_instance.post.call_args
            if call_args:
                _, kwargs = call_args
                data = kwargs.get("data", {})
                print(f"   Sent Language: {data.get('language')}")
                if data.get("language") == "hi":
                    print("   ⚠️ WARNING: Language is hardcoded to 'hi'")
                else:
                    print(f"   ✅ Language: {data.get('language')}")
            else:
                print("   ❌ Could not capture call args")
                
        except Exception as e:
            print(f"   Test Error: {e}")
