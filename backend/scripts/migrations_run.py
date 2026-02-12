
import os
import httpx
from dotenv import load_dotenv

load_dotenv()

SUPABASE_URL = os.getenv("NEXT_PUBLIC_SUPABASE_URL")
SUPABASE_KEY = os.getenv("SUPABASE_SERVICE_ROLE_KEY") # Needs service role key for SQL usually

if not SUPABASE_KEY:
    SUPABASE_KEY = os.getenv("NEXT_PUBLIC_SUPABASE_KEY") # Fallback, might not work for DDL

def run_migration():
    sql = """
    DO $$
    BEGIN
        BEGIN
            ALTER TABLE reminders ADD COLUMN repeat_interval_days INTEGER DEFAULT 7;
        EXCEPTION
            WHEN duplicate_column THEN RAISE NOTICE 'column repeat_interval_days already exists in reminders.';
        END;
        BEGIN
            ALTER TABLE reminders ADD COLUMN next_run TIMESTAMPTZ;
        EXCEPTION
            WHEN duplicate_column THEN RAISE NOTICE 'column next_run already exists in reminders.';
        END;
         BEGIN
            ALTER TABLE reminders ADD COLUMN message TEXT;
        EXCEPTION
            WHEN duplicate_column THEN RAISE NOTICE 'column message already exists in reminders.';
        END;
         BEGIN
            ALTER TABLE reminders ADD COLUMN status TEXT DEFAULT 'pending';
        EXCEPTION
            WHEN duplicate_column THEN RAISE NOTICE 'column status already exists in reminders.';
        END;
    END $$;
    """
    
    print("Running migration via SQL API...")
    # Supabase SQL API is usually /v1/query or executed via client.rpc if function exists.
    # But usually not exposed directly.
    # We will try to use the 'postgres' connection if available or just print instructions if we can't.
    
    print("⚠️  Cannot execute DDL via standard client. Please run the contents of 'migrations/add_reminder_columns.sql' in your Supabase SQL Editor.")

if __name__ == "__main__":
    run_migration()
