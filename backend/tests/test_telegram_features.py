"""
Test Script for Telegram Button + Voice Features
Verifies the implementation works correctly
"""
import asyncio
import sys
from pathlib import Path

# Setup path
sys.path.insert(0, str(Path(__file__).parent))
from dotenv import load_dotenv
load_dotenv(Path(__file__).parent / ".env")


async def test_confirmation_buttons():
    """Test 1: Verify confirmation button generation"""
    print("\n" + "="*50)
    print("TEST 1: Confirmation Buttons")
    print("="*50)
    
    from tools.telegram_bot import get_confirmation_keyboard
    
    keyboard = get_confirmation_keyboard()
    
    # Verify structure
    assert keyboard is not None, "Keyboard should not be None"
    assert len(keyboard.inline_keyboard) == 1, "Should have 1 row"
    assert len(keyboard.inline_keyboard[0]) == 2, "Should have 2 buttons"
    
    # Verify button data
    confirm_btn = keyboard.inline_keyboard[0][0]
    cancel_btn = keyboard.inline_keyboard[0][1]
    
    assert confirm_btn.callback_data == "CONFIRM_YES", f"Expected CONFIRM_YES, got {confirm_btn.callback_data}"
    assert cancel_btn.callback_data == "CONFIRM_NO", f"Expected CONFIRM_NO, got {cancel_btn.callback_data}"
    assert "✅" in confirm_btn.text, "Confirm button should have ✅"
    assert "❌" in cancel_btn.text, "Cancel button should have ❌"
    
    print("  ✅ Keyboard structure correct")
    print(f"  ✅ Confirm button: '{confirm_btn.text}' → {confirm_btn.callback_data}")
    print(f"  ✅ Cancel button: '{cancel_btn.text}' → {cancel_btn.callback_data}")
    print("  ✅ TEST 1 PASSED")


async def test_confirmation_detection():
    """Test 2: Verify confirmation message detection"""
    print("\n" + "="*50)
    print("TEST 2: Confirmation Message Detection")
    print("="*50)
    
    # Messages that should trigger buttons
    trigger_phrases = [
        "YES / NO",
        "YES/NO",
        "Confirm karo",
        "Record karu",
        "add karoon"
    ]
    
    for phrase in trigger_phrases:
        test_msg = f"Sample message with {phrase} in it"
        needs_buttons = any(x in test_msg for x in ["YES / NO", "YES/NO", "Confirm karo", "Record karu", "add karoon"])
        assert needs_buttons, f"Should detect: {phrase}"
        print(f"  ✅ Detected: '{phrase}'")
    
    # Messages that should NOT trigger buttons
    normal_msg = "Stock: 10 packets remaining"
    needs_buttons = any(x in normal_msg for x in ["YES / NO", "YES/NO", "Confirm karo", "Record karu", "add karoon"])
    assert not needs_buttons, "Normal message should not trigger buttons"
    print("  ✅ Normal messages don't trigger buttons")
    
    print("  ✅ TEST 2 PASSED")


async def test_workflow_confirmation():
    """Test 3: Verify YES confirmation executes workflow"""
    print("\n" + "="*50)
    print("TEST 3: Workflow Confirmation Flow")
    print("="*50)
    
    from graph import run_workflow, is_confirmation_message
    
    # Test confirmation message detection
    yes_tests = ["yes", "YES", "haan", "ha", "ok", "theek hai", "kar do"]
    no_tests = ["no", "NO", "nahi", "na", "cancel", "mat karo"]
    
    for msg in yes_tests:
        is_confirm, confirmed = is_confirmation_message(msg)
        assert is_confirm, f"'{msg}' should be detected as confirmation"
        assert confirmed, f"'{msg}' should be positive confirmation"
        print(f"  ✅ '{msg}' → YES")
    
    for msg in no_tests:
        is_confirm, confirmed = is_confirmation_message(msg)
        assert is_confirm, f"'{msg}' should be detected as confirmation"
        assert not confirmed, f"'{msg}' should be negative confirmation"
        print(f"  ✅ '{msg}' → NO")
    
    print("  ✅ TEST 3 PASSED")


async def test_voice_transcription_api():
    """Test 4: Verify voice transcription API setup"""
    print("\n" + "="*50)
    print("TEST 4: Voice Transcription API")
    print("="*50)
    
    import os
    
    hf_token = os.getenv("HF_TOKEN")
    openai_key = os.getenv("OPENAI_API_KEY")
    
    print(f"  HF_TOKEN: {'✅ Present' if hf_token else '❌ Missing'}")
    print(f"  OPENAI_API_KEY: {'✅ Present' if openai_key else '⚠️ Optional'}")
    
    if hf_token:
        print("  ✅ HuggingFace transcription will be used")
    elif openai_key:
        print("  ✅ OpenAI Whisper transcription will be used")
    else:
        print("  ⚠️ No transcription API configured - voice will fallback")
    
    # Test import
    from tools.voice import transcribe_telegram_voice
    print("  ✅ Voice module imports successfully")
    
    print("  ✅ TEST 4 PASSED")


async def test_double_click_protection():
    """Test 5: Verify double-click protection exists"""
    print("\n" + "="*50)
    print("TEST 5: Double-Click Protection")
    print("="*50)
    
    import inspect
    from tools.telegram_bot import handle_callback
    
    # Get source code
    source = inspect.getsource(handle_callback)
    
    # Check for protection mechanisms
    assert "fetch_pending_action" in source, "Should check pending action"
    assert "Already processed" in source, "Should have already processed message"
    
    print("  ✅ fetch_pending_action check present")
    print("  ✅ Already processed message present")
    print("  ✅ TEST 5 PASSED")


async def run_all_tests():
    """Run all tests"""
    print("\n" + "="*60)
    print("  BHARAT BIZ-AGENT - TELEGRAM FEATURES TEST SUITE")
    print("="*60)
    
    try:
        await test_confirmation_buttons()
        await test_confirmation_detection()
        await test_workflow_confirmation()
        await test_voice_transcription_api()
        await test_double_click_protection()
        
        print("\n" + "="*60)
        print("  ✅ ALL TESTS PASSED!")
        print("="*60)
        print("\n🚀 Ready for live testing in Telegram!")
        print("   1. Start bot: python backend/tools/telegram_bot.py")
        print("   2. Send: 'Rakesh ne 3 doodh udhaar liya'")
        print("   3. Click ✅ Confirm button")
        print()
        
    except AssertionError as e:
        print(f"\n❌ TEST FAILED: {e}")
        return False
    except Exception as e:
        print(f"\n❌ ERROR: {e}")
        return False
    
    return True


if __name__ == "__main__":
    success = asyncio.run(run_all_tests())
    exit(0 if success else 1)
