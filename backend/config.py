"""
Configuration with Multi-Provider Support
Supports: Gemini, Grok, Groq Whisper, HuggingFace OCR
"""
import os
from pathlib import Path
from functools import lru_cache
from typing import Optional
from pydantic_settings import BaseSettings
from dotenv import load_dotenv

# Explicitly load .env from backend directory
_backend_dir = Path(__file__).parent
_env_file = _backend_dir / ".env"
load_dotenv(_env_file)

# Also try project root
_root_env = _backend_dir.parent / ".env"
if _root_env.exists():
    load_dotenv(_root_env, override=False)


class MissingEnvError(Exception):
    pass


class Settings(BaseSettings):
    """Application settings from environment variables"""
    
    # Core Required
    supabase_url: str
    supabase_key: str  # Maps to SUPABASE_KEY or SUPABASE_SERVICE_KEY
    
    # LLM Providers (at least one required)
    gemini_api_key: Optional[str] = None
    grok_api_key: Optional[str] = None
    groq_api_key: Optional[str] = None
    
    # Voice/STT
    groq_whisper_api_key: Optional[str] = None
    hf_token: Optional[str] = None
    openai_api_key: Optional[str] = None
    
    # Telegram
    telegram_bot_token: Optional[str] = None

    # Feature Flags
    reminder_runner_enabled: bool = False
    
    @property
    def telegram_enabled(self) -> bool:
        return bool(self.telegram_bot_token)
    
    @property
    def gemini_enabled(self) -> bool:
        return bool(self.gemini_api_key)
    
    @property
    def grok_enabled(self) -> bool:
        return bool(self.grok_api_key)
    
    @property
    def groq_enabled(self) -> bool:
        return bool(self.groq_api_key)
    
    @property
    def whisper_enabled(self) -> bool:
        return bool(self.groq_api_key or self.groq_whisper_api_key or self.openai_api_key)
    
    @property
    def ocr_enabled(self) -> bool:
        return bool(self.hf_token)
    
    class Config:
        env_file = ".env"
        case_sensitive = False
        extra = "ignore"


def mask_secret(val: str) -> str:
    """Mask secret for display"""
    if not val:
        return "Not set"
    return val[:8] + "..." if len(val) > 12 else "***"


def validate_required_env():
    """Validate required environment variables"""
    # Check essential keys
    required = {
        "SUPABASE_URL": os.getenv("SUPABASE_URL"),
        # Startups might use SUPABASE_KEY or SUPABASE_SERVICE_KEY
        "SUPABASE_KEY": os.getenv("SUPABASE_KEY") or os.getenv("SUPABASE_SERVICE_KEY"),
    }
    
    # At least one LLM required
    llm_keys = {
        "GEMINI_API_KEY": os.getenv("GEMINI_API_KEY"),
        "GROK_API_KEY": os.getenv("GROK_API_KEY"),
        "GROQ_API_KEY": os.getenv("GROQ_API_KEY"),
    }
    
    print("\n🔐 Environment Variables Status:")
    print("━" * 40)
    
    # Core required
    missing = []
    for var, val in required.items():
        if val:
            print(f"  ✅ {var}: {mask_secret(val)}")
        else:
            print(f"  ❌ {var}: Missing!")
            missing.append(var)
    
    # LLM providers
    print("\n📡 LLM Providers:")
    llm_available = False
    for var, val in llm_keys.items():
        if val:
            print(f"  ✅ {var}: {mask_secret(val)}")
            llm_available = True
        else:
            print(f"  ⚪ {var}: Not configured")
    
    if not llm_available:
        print("  ⚠️ No LLM API keys - will use regex fallback only")
    
    # Voice/OCR
    print("\n🎤 Voice & OCR:")
    voice_keys = {
        "GROQ_WHISPER_API_KEY": os.getenv("GROQ_WHISPER_API_KEY") or os.getenv("GROQ_API_KEY"),
        "HF_TOKEN (OCR)": os.getenv("HF_TOKEN"),
        "OPENAI_API_KEY": os.getenv("OPENAI_API_KEY"),
    }
    for var, val in voice_keys.items():
        status = "✅" if val else "⚪"
        print(f"  {status} {var}: {'Enabled' if val else 'Not configured'}")
    
    # Telegram
    print("\n📱 Telegram:")
    tg_token = os.getenv("TELEGRAM_BOT_TOKEN")
    if tg_token:
        print(f"  ✅ TELEGRAM_BOT_TOKEN: {mask_secret(tg_token)}")
    else:
        print("  ⚪ TELEGRAM_BOT_TOKEN: Not configured (Optional)")
    
    print("━" * 40)
    
    if missing:
        error_msg = f"\n❌ Missing required: {', '.join(missing)}"
        error_msg += f"\nSet them in: {_env_file}"
        raise MissingEnvError(error_msg)


def print_startup_status():
    """Print clean startup status"""
    print("\n" + "=" * 50)
    print("  🚀 BHARAT BIZ-AGENT - SYSTEM STATUS")
    print("=" * 50)
    
    statuses = []
    
    # LLM
    if os.getenv("GEMINI_API_KEY"):
        statuses.append("✅ Gemini LLM: Enabled")
    else:
        statuses.append("⚠️ Gemini LLM: Disabled")
    
    # Grok/Groq
    if os.getenv("GROK_API_KEY"): statuses.append("✅ Grok Fallback: Enabled")
    if os.getenv("GROQ_API_KEY"): statuses.append("✅ Groq LLM: Enabled")

    # Voice/OCR
    if os.getenv("GROQ_WHISPER_API_KEY") or os.getenv("GROQ_API_KEY"):
        statuses.append("✅ Whisper: Enabled")
    
    if os.getenv("HF_TOKEN"):
        statuses.append("✅ HuggingFace OCR: Enabled")
    
    # Feature Flags
    if os.getenv("REMINDER_RUNNER_ENABLED", "false").lower() == "true":
         statuses.append("⏰ Reminder Runner: ACTIVE")
    else:
         statuses.append("💤 Reminder Runner: Disabled (Safety Mode)")

    
    # Always available
    statuses.append("✅ Regex Fallback: Always available")
    
    for s in statuses:
        print(f"  {s}")
    
    print("=" * 50 + "\n")


@lru_cache()
def get_settings() -> Settings:
    """Get cached settings instance"""
    validate_required_env()
    return Settings()


# Initialize on import
try:
    settings = get_settings()
    print_startup_status()
except MissingEnvError as e:
    print(e)
    # Don't fail immediately on import, fail on usage or let main.py handle it
    settings = None
except Exception as e:
    print(f"❌ Config error: {e}")
    settings = None
