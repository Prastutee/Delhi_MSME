"""
Voice Transcription - FORCES Groq Whisper
DEBUG: Full logging for every API call
"""
import os
import httpx
import traceback
from pathlib import Path
from dotenv import load_dotenv

# Load env
_backend = Path(__file__).parent.parent
load_dotenv(_backend / ".env")

print("\n" + "=" * 50)
print("🎤 VOICE MODULE - STT STATUS")
print("=" * 50)
_groq_key = os.getenv("GROQ_WHISPER_API_KEY") or os.getenv("GROQ_API_KEY")
print(f"   GROQ_WHISPER_API_KEY: {_groq_key[:15]}..." if _groq_key else "   GROQ_WHISPER_API_KEY: ❌ MISSING")
print(f"   HF_TOKEN: {'✅ Set' if os.getenv('HF_TOKEN') else '❌ MISSING'}")
print("=" * 50)


async def transcribe_telegram_voice(file_url: str) -> str:
    """
    Transcribe voice - Groq Whisper primary
    Full debug logging on every step
    """
    print(f"\n{'='*50}")
    print("🎤 VOICE TRANSCRIPTION REQUEST")
    print("="*50)
    print(f"   URL: {file_url}")
    
    # Step 1: Download
    print("\n📥 STEP 1: Downloading audio...")
    audio_data = await download_audio(file_url)
    if not audio_data:
        print("   ❌ Download failed!")
        return "[Download failed - please type message]"
    print(f"   ✅ Downloaded {len(audio_data)} bytes")
    
    # Step 2: Groq Whisper
    groq_key = os.getenv("GROQ_WHISPER_API_KEY") or os.getenv("GROQ_API_KEY")
    if groq_key:
        print(f"\n🎯 STEP 2: Calling Groq Whisper...")
        print(f"   API Key: {groq_key[:15]}...")
        # Telegram defaults to Hindi/Hinglish
        result = await transcribe_groq_whisper(audio_data, groq_key, language="hi")
        if result and not result.startswith("["):
            print(f"   ✅ GROQ SUCCESS: {result}")
            return result
        print(f"   ❌ Groq failed: {result}")
    else:
        print("\n⚠️ STEP 2: No Groq API key, skipping...")
    
    # Step 3: HuggingFace fallback
    hf_token = os.getenv("HF_TOKEN")
    if hf_token:
        print(f"\n🎯 STEP 3: Calling HuggingFace Whisper...")
        result = await transcribe_huggingface(audio_data, hf_token)
        if result and not result.startswith("["):
            print(f"   ✅ HF SUCCESS: {result}")
            return result
        print(f"   ❌ HF failed: {result}")
    
    print("\n❌ ALL TRANSCRIPTION METHODS FAILED")
    return "[Transcription failed - please type message]"


async def download_audio(file_url: str) -> bytes:
    """Download audio from Telegram"""
    try:
        async with httpx.AsyncClient(timeout=30) as client:
            response = await client.get(file_url)
            print(f"   HTTP Status: {response.status_code}")
            if response.status_code == 200:
                return response.content
            print(f"   Error body: {response.text[:100]}")
    except Exception as e:
        print(f"   Exception: {e}")
    return None


async def transcribe_groq_whisper(audio_data: bytes, api_key: str, language: str = "hi") -> str:
    """
    Call Groq Whisper API
    Endpoint: https://api.groq.com/openai/v1/audio/transcriptions
    """
    url = "https://api.groq.com/openai/v1/audio/transcriptions"
    
    print(f"   Endpoint: {url}")
    print(f"   Audio size: {len(audio_data)} bytes")
    print(f"   Model: whisper-large-v3")
    print(f"   Language: {language}")
    
    try:
        # Multipart form data
        files = {
            "file": ("voice.ogg", audio_data, "audio/ogg"),
        }
        data = {
            "model": "whisper-large-v3",
            "language": language,
            "response_format": "json"
        }
        headers = {
            "Authorization": f"Bearer {api_key}"
        }
        
        print("   Sending request...")
        
        async with httpx.AsyncClient(timeout=60) as client:
            response = await client.post(
                url,
                headers=headers,
                files=files,
                data=data
            )
            
            print(f"   Response Status: {response.status_code}")
            print(f"   Response Body: {response.text[:300]}")
            
            if response.status_code == 200:
                result = response.json()
                text = result.get("text", "").strip()
                if text:
                    return text
                return "[Empty transcription]"
            elif response.status_code == 401:
                return "[Groq: Invalid API key]"
            elif response.status_code == 429:
                return "[Groq: Rate limited]"
            else:
                return f"[Groq error: {response.status_code}]"
                
    except httpx.TimeoutException:
        print("   ❌ Timeout!")
        return "[Groq: Timeout]"
    except Exception as e:
        print(f"   ❌ Exception: {e}")
        traceback.print_exc()
        return f"[Groq exception]"


async def transcribe_huggingface(audio_data: bytes, token: str) -> str:
    """HuggingFace Whisper fallback"""
    url = "https://api-inference.huggingface.co/models/openai/whisper-small"
    
    print(f"   Endpoint: {url}")
    
    try:
        headers = {
            "Authorization": f"Bearer {token}",
            "Content-Type": "audio/ogg"
        }
        
        async with httpx.AsyncClient(timeout=60) as client:
            response = await client.post(url, headers=headers, content=audio_data)
            
            print(f"   Response Status: {response.status_code}")
            print(f"   Response Body: {response.text[:200]}")
            
            if response.status_code == 200:
                result = response.json()
                if isinstance(result, dict) and "text" in result:
                    return result["text"].strip()
                elif isinstance(result, list) and len(result) > 0:
                    return result[0].get("text", "").strip()
            
            if response.status_code == 503:
                return "[HF: Model loading]"
                
    except Exception as e:
        print(f"   ❌ Exception: {e}")
    
    return "[HuggingFace failed]"


# Alias
async def transcribe_audio(file_url: str) -> str:
    return await transcribe_telegram_voice(file_url)

async def transcribe_audio_groq(audio_bytes: bytes, language: str = "en") -> str:
    """
    Direct transcription of audio bytes using Groq Whisper
    Used by Dashboard Voice Input (Default: English)
    """
    groq_key = os.getenv("GROQ_WHISPER_API_KEY") or os.getenv("GROQ_API_KEY")
    if not groq_key:
        return "[Error: Missing Groq API Key]"
        
    return await transcribe_groq_whisper(audio_bytes, groq_key, language=language)
