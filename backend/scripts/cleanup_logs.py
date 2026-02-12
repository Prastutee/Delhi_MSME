import asyncio
from db import get_db

async def cleanup_logs():
    print("🧹 CLEANING UP LOGS...")
    db = get_db()
    
    # Business-allowed types
    ALLOWED_ACTIONS = [
        "sale_credit", "sale_paid", "payment", "purchase", 
        "inventory_update", "reminder_created", "reminder_scheduled", 
        "reminder_sent", "low_stock_alert", "system_start", "payment_received", "error"
    ]
    
    # 1. Fetch all logs
    try:
        all_logs = db.table("logs").select("id, action_type, message").execute().data
        print(f"   Found {len(all_logs)} total logs")
        
        deleted = 0
        for log in all_logs:
            action = log["action_type"]
            msg = log["message"] or ""
            
            # Check if this log should be deleted
            should_delete = False
            
            if action not in ALLOWED_ACTIONS:
                should_delete = True
            
            # Specific keyword filters
            if "[Gemini]" in msg or "[Groq]" in msg or "LLM" in msg:
                 should_delete = True
                 
            if should_delete:
                print(f"   ❌ Deleting: [{action}] {msg[:40]}...")
                db.table("logs").delete().eq("id", log["id"]).execute()
                deleted += 1
                
        print(f"✅ Cleanup complete. Removed {deleted} logs.")
        
    except Exception as e:
        print(f"❌ Error during cleanup: {e}")

if __name__ == "__main__":
    asyncio.run(cleanup_logs())
