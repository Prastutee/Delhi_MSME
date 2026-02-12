"""
Telegram Bot - Full Debug Logging
Voice: Groq Whisper → HF fallback
Text: Gemini → Grok → Regex
"""
from telegram import Update, Bot, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import (
    Application, 
    CommandHandler, 
    MessageHandler, 
    CallbackQueryHandler,
    filters,
    ContextTypes
)
from typing import Optional
import os
import sys
import traceback
from pathlib import Path
from dotenv import load_dotenv

# Load environment
_backend = Path(__file__).parent.parent
load_dotenv(_backend / ".env")
sys.path.insert(0, str(_backend))

print("\n" + "=" * 50)
print("📱 TELEGRAM BOT - STARTING")
print("=" * 50)

_bot: Optional[Bot] = None


def get_bot() -> Optional[Bot]:
    global _bot
    if _bot is None:
        token = os.getenv("TELEGRAM_BOT_TOKEN")
        if token:
            _bot = Bot(token=token)
    return _bot


# ============================================
# KEYBOARDS
# ============================================

def get_confirmation_keyboard() -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup([
        [
            InlineKeyboardButton("✅ Confirm", callback_data="CONFIRM_YES"),
            InlineKeyboardButton("❌ Cancel", callback_data="CONFIRM_NO"),
        ]
    ])


def needs_buttons(response: str) -> bool:
    return any(t in response for t in ["YES / NO", "YES/NO", "?"])


async def send_with_buttons(chat_id: str, message: str):
    bot = get_bot()
    if not bot:
        return
    try:
        await bot.send_message(chat_id=chat_id, text=message, parse_mode="Markdown", reply_markup=get_confirmation_keyboard())
    except:
        try:
            await bot.send_message(chat_id=chat_id, text=message, reply_markup=get_confirmation_keyboard())
        except Exception as e:
            print(f"   Send error: {e}")


# ============================================
# CALLBACK HANDLER
# ============================================

async def handle_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    from graph import run_workflow
    from db import log_chat, fetch_pending_action
    
    query = update.callback_query
    chat_id = str(update.effective_chat.id)
    
    print(f"\n🔘 BUTTON: {query.data} from {chat_id}")
    
    pending = await fetch_pending_action(chat_id)
    if not pending:
        # FIX 6: Exact expected message
        await query.answer("Already processed")
        try:
            # FIX 6: Use correct edit method handling for captions
            if query.message.caption:
                await query.edit_message_caption(caption=query.message.caption + "\n\n_✅ Done_", parse_mode="Markdown")
            else:
                await query.edit_message_text(text=query.message.text + "\n\n_✅ Done_", parse_mode="Markdown")
        except:
            pass
        return
    
    await query.answer()
    
    if query.data == "CONFIRM_YES":
        await log_chat(chat_id, "telegram", "[✅ Confirm]", "incoming")
        response = await run_workflow(chat_id, "YES")
    elif query.data == "CONFIRM_NO":
        await log_chat(chat_id, "telegram", "[❌ Cancel]", "incoming")
        response = await run_workflow(chat_id, "NO")
    else:
        response = "Unknown"
    
    print(f"   Response: {response[:60]}...")
    await log_chat(chat_id, "telegram", response, "outgoing")
    
    try:
        # FIX 6: Handle photo captions vs text messages
        if query.message.caption:
             await query.message.reply_text(response, parse_mode="Markdown")
        else:
             await query.edit_message_text(response, parse_mode="Markdown")
    except:
        await query.message.reply_text(response)


# ============================================
# COMMANDS
# ============================================

async def cmd_start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    from db import get_or_create_customer, log_chat
    
    user = update.effective_user
    chat_id = str(update.effective_chat.id)
    
    print(f"\n👋 /start from {user.first_name}")
    
    await get_or_create_customer(chat_id, user.first_name or "")
    
    msg = f"""🙏 *Namaste {user.first_name}!*

Main *Bharat Biz-Agent* hoon.

*Try:*
• "Rakesh ne 3 doodh udhaar liya"
• "Sharma ne 500 diya"
• Voice note bhejo
• Receipt photo bhejo

Hinglish mein baat karo! 😊"""
    
    await log_chat(chat_id, "telegram", "/start", "incoming")
    await update.message.reply_text(msg, parse_mode="Markdown")


async def cmd_stock(update: Update, context: ContextTypes.DEFAULT_TYPE):
    from db import list_inventory
    
    print(f"\n📦 /stock command")
    
    items = await list_inventory()
    if not items:
        await update.message.reply_text("📦 Empty")
        return
    
    msg = "📦 *Stock:*\n\n"
    for item in items[:10]:
        msg += f"• {item['item_name']}: {item['quantity']}\n"
    
    await update.message.reply_text(msg, parse_mode="Markdown")


# ============================================
# TEXT HANDLER
# ============================================

async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    from graph import run_workflow
    from db import log_chat
    
    chat_id = str(update.effective_chat.id)
    text = update.message.text
    
    if not text:
        return

    print(f"\n{'='*50}")
    print(f"💬 TEXT MESSAGE")
    print(f"   From: {chat_id}")
    print(f"   Text: {text}")
    print("="*50)
    
    await log_chat(chat_id, "telegram", text, "incoming")
    
    try:
        response = await run_workflow(chat_id, text)
        print(f"\n📤 RESPONSE: {response}")
    except Exception as e:
        print(f"   ❌ Workflow error: {e}")
        traceback.print_exc()
        response = "⚠️ Error, try again!"
    
    await log_chat(chat_id, "telegram", response, "outgoing")
    
    if needs_buttons(response):
        print("   📱 Sending with buttons")
        await send_with_buttons(chat_id, response)
    else:
        try:
            await update.message.reply_text(response, parse_mode="Markdown")
        except:
            await update.message.reply_text(response)


# ============================================
# VOICE HANDLER - FORCES GROQ WHISPER
# ============================================

async def handle_voice(update: Update, context: ContextTypes.DEFAULT_TYPE):
    from graph import run_workflow
    from db import log_chat
    from tools.voice import transcribe_telegram_voice
    
    chat_id = str(update.effective_chat.id)
    
    print(f"\n{'='*50}")
    print("🎤 VOICE MESSAGE RECEIVED")
    print(f"   From: {chat_id}")
    print("="*50)
    
    voice = update.message.voice
    file = await context.bot.get_file(voice.file_id)
    
    print(f"   File ID: {voice.file_id}")
    print(f"   File path: {file.file_path}")
    
    if not file.file_path:
        await update.message.reply_text("❌ Voice error")
        return
    
    processing = await update.message.reply_text("🎤 Processing voice...")
    
    # FORCE CALL GROQ WHISPER
    print("\n🎤 CALLING GROQ WHISPER NOW...")
    try:
        text = await transcribe_telegram_voice(file.file_path)
        print(f"\n📝 TRANSCRIPT RESULT: {text}")
    except Exception as e:
        print(f"   ❌ Transcription exception: {e}")
        traceback.print_exc()
        text = "[Transcription error]"
    
    if not text or text.startswith("["):
        await processing.edit_text(f"⚠️ {text}\n\nPlease type message.")
        return
    
    await processing.edit_text(f"🎤 Heard: _{text}_")
    await log_chat(chat_id, "telegram", f"[Voice] {text}", "incoming")
    
    # Now process through workflow
    print(f"\n📤 Sending to workflow: {text}")
    try:
        response = await run_workflow(chat_id, text)
        print(f"📥 Workflow response: {response}")
    except Exception as e:
        print(f"   ❌ Workflow error: {e}")
        response = "⚠️ Error processing"
    
    await log_chat(chat_id, "telegram", response, "outgoing")
    
    if needs_buttons(response):
        await send_with_buttons(chat_id, response)
    else:
        try:
            await update.message.reply_text(response, parse_mode="Markdown")
        except:
            await update.message.reply_text(response)


# ============================================
# PHOTO HANDLER
# ============================================

async def handle_photo(update: Update, context: ContextTypes.DEFAULT_TYPE):
    from graph import run_workflow
    from db import log_chat
    
    chat_id = str(update.effective_chat.id)
    caption = update.message.caption or "Receipt photo"
    
    print(f"\n📷 PHOTO from {chat_id}: {caption}")
    
    await log_chat(chat_id, "telegram", f"[Photo] {caption}", "incoming")
    
    response = await run_workflow(chat_id, caption)
    await log_chat(chat_id, "telegram", response, "outgoing")
    
    if needs_buttons(response):
        await send_with_buttons(chat_id, response)
    else:
        await update.message.reply_text(response)


# ============================================
# ERROR HANDLER
# ============================================

async def error_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    print(f"\n❌ BOT ERROR: {context.error}")
    traceback.print_exc()
    
    if update and update.effective_chat:
        try:
            await context.bot.send_message(chat_id=update.effective_chat.id, text="⚠️ Error, try again!")
        except:
            pass


# ============================================
# MAIN
# ============================================

def run_telegram_bot():
    from db import log_event
    
    token = os.getenv("TELEGRAM_BOT_TOKEN")
    if not token:
        print("❌ TELEGRAM_BOT_TOKEN not set!")
        return
    
    print("\n" + "=" * 60)
    print("🤖 BHARAT BIZ-AGENT - READY")
    print("=" * 60)
    print("   Mode: Polling")
    print("   Debug: FULL LOGGING")
    print("   Voice: Groq Whisper → HF")
    print("   Text: Gemini → Grok → Regex")
    print("=" * 60 + "\n")
    
    app = Application.builder().token(token).build()
    
    app.add_handler(CommandHandler("start", cmd_start))
    app.add_handler(CommandHandler("stock", cmd_stock))
    app.add_handler(CallbackQueryHandler(handle_callback))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message))
    app.add_handler(MessageHandler(filters.VOICE, handle_voice))
    app.add_handler(MessageHandler(filters.PHOTO, handle_photo))
    app.add_error_handler(error_handler)
    
    log_event("system", "Bot started - full debug mode")
    
    app.run_polling(allowed_updates=Update.ALL_TYPES)


if __name__ == "__main__":
    run_telegram_bot()
