"""
Autonomous Reminder Runner
Checks for due reminders and sends them via Telegram
"""
import asyncio
from datetime import datetime, timedelta
import sys
import os
import traceback

# Add parent to path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from db import get_db, log_event
from backend.tools.telegram_bot import send_text
from config import settings

async def process_reminders():
    if not settings.reminder_runner_enabled:
        print("💤 Reminder Runner is DISABLED (Safety Mode)")
        return

    print("\n" + "="*50)
    print("⏰ AUTONOMOUS REMINDER RUNNER")
    print("="*50)
    
    try:
        db = get_db()
        now = datetime.utcnow().isoformat()
        
        # Find due reminders
        # Note: We select specific columns to avoid error if schema drift, but * is usually safer if we aligned via migrations
        due = db.table("reminders") \
            .select("*, customers(phone)") \
            .eq("status", "pending") \
            .lte("next_run", now) \
            .execute().data
            
        print(f"   Found {len(due)} due reminders")

        for r in due:
            try:
                customer_phone = r["customers"]["phone"] if r.get("customers") else None
                
                if customer_phone:
                    message = f"⏰ Reminder: {r.get('message', 'Payment Due')}"
                    print(f"   Sending to {customer_phone}: {message}")
                    
                    # Send telegram message
                    await send_text(
                        chat_id=customer_phone,
                        message=message
                    )
                    
                    # Reschedule
                    interval = r.get("repeat_interval_days", 7) or 7
                    next_run = datetime.utcnow() + timedelta(days=interval)

                    # Update next_run and keep status pending (it's a recurring reminder)
                    # Or should we mark as 'sent' and create a NEW record?
                    # The prompt says: "reschedule next_run += repeat_interval_days"
                    # This implies keeping the same record and just bumping the date.
                    
                    db.table("reminders").update({
                        "next_run": next_run.isoformat(),
                        # We don't change status to 'sent' because it's recurring.
                        # Unless it's a one-time reminder? 
                        # User prompt: "reschedule next_run += repeat_interval_days"
                    }).eq("id", r["id"]).execute()
                    
                    from db import log_business_event
                    log_business_event("reminder_sent", f"Sent autonomous reminder to {customer_phone}", channel="reminder_runner")
                else:
                    print(f"   ⚠️ No phone for customer {r.get('customer_id', 'unknown')}")
                    
            except Exception as e:
                print(f"   ❌ Error processing reminder {r.get('id', 'unknown')}: {e}")
                traceback.print_exc()

        print("✅ Reminder cycle complete")
        
    except Exception as e:
        print(f"❌ Runner Error: {e}")
        traceback.print_exc()

if __name__ == "__main__":
    asyncio.run(process_reminders())
