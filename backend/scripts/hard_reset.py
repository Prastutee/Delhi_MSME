import asyncio
from db import get_db

async def hard_reset():
    print("🧨 STARTING HARD RESET (DATA WIPE)...")
    db = get_db()
    
    tables = ["logs", "reminders", "transactions"]
    
    for table in tables:
        try:
            print(f"   Cleaning {table}...")
            # Supabase delete all (using filter on id is not null if possible, or iterating)
            # Safer: fetch IDs then delete
            res = db.table(table).select("id").execute()
            ids = [row['id'] for row in res.data]
            
            if ids:
                # Delete in chunks
                for i in range(0, len(ids), 100):
                    batch = ids[i:i+100]
                    db.table(table).delete().in_("id", batch).execute()
                print(f"   ✅ Deleted {len(ids)} rows from {table}")
            else:
                print(f"   ✅ {table} is already empty")
                
        except Exception as e:
            print(f"   ❌ Error cleaning {table}: {e}")

if __name__ == "__main__":
    asyncio.run(hard_reset())
