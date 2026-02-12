import asyncio
import sys
import os
import json

# Add parent to path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from db import get_db

async def audit_schema():
    print("🔍 AUDITING SUPABASE SCHEMA")
    db = get_db()
    
    tables = ['reminders', 'customers', 'transactions', 'inventory', 'suppliers', 'logs']
    
    # Method 1: Try querying information_schema (often restricted in Supabase client but worth a try via rpc if we had one, or just standard select if exposed)
    # The client usually queries 'public' schema by default. Accessing information_schema might be tricky.
    # We will try to just select * from the table with limit 1 and print keys.
    
    for table in tables:
        print(f"\n--- Table: {table} ---")
        try:
            # Try to fetch one row
            res = db.table(table).select("*").limit(1).execute()
            if res.data and len(res.data) > 0:
                keys = res.data[0].keys()
                print(f"✅ Found columns: {list(keys)}")
                # Check specific types if possible? 
                # We can't easily check types without inserting/reading. 
                # But knowing columns is 90% of the battle.
            else:
                print("⚠️ Table exists but is empty. Cannot infer columns from data.")
                # If empty, we might try to INSERT a dummy row to see if it accepts columns, but that's risky data pollution.
        except Exception as e:
            print(f"❌ Error accessing table: {e}")

if __name__ == "__main__":
    asyncio.run(audit_schema())
