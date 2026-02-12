import asyncio
from db import get_db

async def verify_schema():
    print("🔍 VERIFYING REMINDERS SCHEMA...")
    # Since we can't run raw SQL easily via client on information_schema for some setups,
    # we will inspect a dummy insert failure or select * 
    
    db = get_db()
    
    REQUIRED_COLUMNS = [
        "id", "customer_id", "reminder_type", "message", 
        "status", "next_run", "repeat_interval_days", "created_at"
    ]
    
    try:
        # Try to select all required columns (limit 0)
        sel = ", ".join(REQUIRED_COLUMNS)
        print(f"   Checking columns: {sel}")
        db.table("reminders").select(sel).limit(1).execute()
        print("✅ Schema check passed: All columns exist/accessible.")
        
    except Exception as e:
        print(f"❌ Schema Verification Failed: {e}")
        print("   Migration likely needed.")

if __name__ == "__main__":
    asyncio.run(verify_schema())
