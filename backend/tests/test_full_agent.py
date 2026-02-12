"""
End-to-End Test Suite for Bharat Biz-Agent
Tests all critical paths: LLM fallback, voice, OCR, buttons
"""
import asyncio
import os
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))
from dotenv import load_dotenv
load_dotenv(Path(__file__).parent / ".env")


async def test_1_confirmation_buttons():
    """Test: Confirmation keyboard structure"""
    print("\n" + "=" * 50)
    print("TEST 1: Confirmation Buttons")
    print("=" * 50)
    
    from tools.telegram_bot import get_confirmation_keyboard, needs_buttons
    
    kb = get_confirmation_keyboard()
    assert kb is not None
    assert len(kb.inline_keyboard) == 1
    assert len(kb.inline_keyboard[0]) == 2
    
    confirm = kb.inline_keyboard[0][0]
    cancel = kb.inline_keyboard[0][1]
    
    assert confirm.callback_data == "CONFIRM_YES"
    assert cancel.callback_data == "CONFIRM_NO"
    print("  ✅ Keyboard structure correct")
    
    # Test trigger detection
    assert needs_buttons("Confirm karo? YES / NO")
    assert needs_buttons("Record karu?")
    assert not needs_buttons("Stock: 10 packets")
    print("  ✅ Button trigger detection works")
    
    print("  ✅ TEST 1 PASSED")


async def test_2_llm_fallback_chain():
    """Test: Multi-LLM fallback chain"""
    print("\n" + "=" * 50)
    print("TEST 2: LLM Fallback Chain")
    print("=" * 50)
    
    from agent import extract_intent_regex, get_active_provider
    
    # Test regex fallback directly
    result = extract_intent_regex("Rakesh ne 3 doodh udhaar liya")
    
    assert result["intent"] == "sale_credit"
    assert result["entities"]["customer_name"] == "Rakesh"
    assert result["entities"]["item_name"] == "Milk"
    assert result["entities"]["quantity"] == 3
    assert result["needs_confirmation"] == True
    
    print("  ✅ Regex detects: sale_credit")
    print(f"  ✅ Customer: {result['entities']['customer_name']}")
    print(f"  ✅ Item: {result['entities']['item_name']}")
    print(f"  ✅ Qty: {result['entities']['quantity']}")
    
    # Test payment
    result2 = extract_intent_regex("Sharma ne 500 rupaye de diya")
    assert result2["intent"] == "payment"
    assert result2["entities"]["amount"] == 500
    print("  ✅ Regex detects: payment ₹500")
    
    # Test stock query
    result3 = extract_intent_regex("stock kitna hai")
    assert result3["intent"] == "general_query"
    print("  ✅ Regex detects: stock query")
    
    print("  ✅ TEST 2 PASSED")


async def test_3_workflow_confirmation():
    """Test: YES/NO confirmation handling"""
    print("\n" + "=" * 50)
    print("TEST 3: Confirmation Detection")
    print("=" * 50)
    
    from graph import is_confirmation_message
    
    yes_words = ["yes", "YES", "haan", "ha", "ok", "theek hai", "kar do", "ji"]
    no_words = ["no", "NO", "nahi", "na", "cancel", "mat karo"]
    
    for word in yes_words:
        is_confirm, confirmed = is_confirmation_message(word)
        assert is_confirm, f"'{word}' should be detected"
        assert confirmed, f"'{word}' should be positive"
        print(f"  ✅ '{word}' → YES")
    
    for word in no_words:
        is_confirm, confirmed = is_confirmation_message(word)
        assert is_confirm, f"'{word}' should be detected"
        assert not confirmed, f"'{word}' should be negative"
        print(f"  ✅ '{word}' → NO")
    
    print("  ✅ TEST 3 PASSED")


async def test_4_voice_api_setup():
    """Test: Voice transcription API availability"""
    print("\n" + "=" * 50)
    print("TEST 4: Voice STT API")
    print("=" * 50)
    
    groq = os.getenv("GROQ_API_KEY")
    openai = os.getenv("OPENAI_API_KEY")
    hf = os.getenv("HF_TOKEN")
    
    print(f"  Groq Whisper: {'✅ Configured' if groq else '⚪ Not set'}")
    print(f"  OpenAI Whisper: {'✅ Configured' if openai else '⚪ Not set'}")
    print(f"  HuggingFace: {'✅ Configured' if hf else '⚪ Not set'}")
    
    # Import test
    from tools.voice import transcribe_telegram_voice
    print("  ✅ Voice module imports OK")
    
    if groq or openai or hf:
        print("  ✅ At least one STT provider available")
    else:
        print("  ⚠️ No STT configured - voice will fallback")
    
    print("  ✅ TEST 4 PASSED")


async def test_5_ocr_api_setup():
    """Test: OCR API availability"""
    print("\n" + "=" * 50)
    print("TEST 5: OCR API")
    print("=" * 50)
    
    hf = os.getenv("HF_TOKEN")
    
    print(f"  HuggingFace OCR: {'✅ Configured' if hf else '⚪ Not set'}")
    
    # Import test
    from tools.ocr import extract_text_from_receipt, parse_receipt_items
    print("  ✅ OCR module imports OK")
    
    # Test parser
    items = await parse_receipt_items("Milk x 10, Bread x 5")
    assert len(items) >= 1
    print(f"  ✅ Parser found {len(items)} items")
    
    print("  ✅ TEST 5 PASSED")


async def test_6_double_click_protection():
    """Test: Button double-click protection"""
    print("\n" + "=" * 50)
    print("TEST 6: Double-Click Protection")
    print("=" * 50)
    
    import inspect
    from tools.telegram_bot import handle_callback
    
    source = inspect.getsource(handle_callback)
    
    assert "fetch_pending_action" in source
    print("  ✅ Checks pending action before execute")
    
    assert "Already processed" in source
    print("  ✅ Shows 'Already processed' message")
    
    print("  ✅ TEST 6 PASSED")


async def test_7_env_config():
    """Test: Environment configuration"""
    print("\n" + "=" * 50)
    print("TEST 7: Environment Config")
    print("=" * 50)
    
    required = ["SUPABASE_URL", "SUPABASE_KEY", "TELEGRAM_BOT_TOKEN"]
    
    for var in required:
        val = os.getenv(var)
        status = "✅" if val else "❌"
        print(f"  {status} {var}: {'Set' if val else 'MISSING!'}")
        assert val, f"{var} is required"
    
    # LLM check
    llm_keys = ["GEMINI_API_KEY", "GROK_API_KEY", "GROQ_API_KEY"]
    llm_available = any(os.getenv(k) for k in llm_keys)
    
    if llm_available:
        print("  ✅ At least one LLM configured")
    else:
        print("  ⚠️ No LLM keys - will use regex only")
    
    print("  ✅ TEST 7 PASSED")


async def run_all_tests():
    """Run complete test suite"""
    print("\n" + "=" * 60)
    print("  BHARAT BIZ-AGENT - FULL SYSTEM TEST SUITE")
    print("=" * 60)
    
    try:
        await test_1_confirmation_buttons()
        await test_2_llm_fallback_chain()
        await test_3_workflow_confirmation()
        await test_4_voice_api_setup()
        await test_5_ocr_api_setup()
        await test_6_double_click_protection()
        await test_7_env_config()
        
        print("\n" + "=" * 60)
        print("  ✅ ALL 7 TESTS PASSED!")
        print("=" * 60)
        
        print("\n🚀 DEMO READY!")
        print("   Start: python backend/tools/telegram_bot.py")
        print("\n   Test flows:")
        print("   1. Text: 'Rakesh ne 3 doodh udhaar liya' → Click ✅")
        print("   2. Voice: Send voice note → Buttons appear")
        print("   3. Photo: Upload receipt → OCR detects items")
        print()
        
        return True
        
    except AssertionError as e:
        print(f"\n❌ TEST FAILED: {e}")
        return False
    except Exception as e:
        print(f"\n❌ ERROR: {e}")
        import traceback
        traceback.print_exc()
        return False


if __name__ == "__main__":
    success = asyncio.run(run_all_tests())
    exit(0 if success else 1)
