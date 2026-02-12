import asyncio
from db import get_db

async def wipe_logs():
    print("🧨 WIPING ALL LOGS...")
    db = get_db()
    
    try:
        # Delete all rows in logs table
        # Supabase delete without where clause needs some trick or just neq regex
        # simpler: delete where id is not null (if allowed) or iterating
        
        # Taking a safer approach: Select IDs then delete
        print("   Fetching logs...")
        res = db.table("logs").select("id").execute()
        ids = [row['id'] for row in res.data]
        
        if ids:
            print(f"   Deleting {len(ids)} logs...")
            # Delete in chunks if needed, but for now strict delete
            for i in range(0, len(ids), 100):
                batch = ids[i:i+100]
                db.table("logs").delete().in_("id", batch).execute()
        
        print("✅ Logs wiped successfully.")
        
    except Exception as e:
        print(f"❌ Error wiping logs: {e}")

if __name__ == "__main__":
    asyncio.run(wipe_logs())
