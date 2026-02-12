
import os
import httpx
from dotenv import load_dotenv

load_dotenv()

# We need to use the Pooler URL or Direct URL for DDL
# "postgres://postgres.[project-ref]:[password]@aws-0-[region].pooler.supabase.com:6543/postgres"

DATABASE_URL = os.getenv("DATABASE_URL")

def apply_schema():
    print("🚀 Applying Schema Fixes...")
    
    # Minimal SQL to fix missing tables
    sql = """
    CREATE EXTENSION IF NOT EXISTS "uuid-ossp";

    CREATE TABLE IF NOT EXISTS chat_logs (
        id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
        user_phone TEXT NOT NULL,
        channel TEXT NOT NULL,
        direction TEXT CHECK (direction IN ('incoming', 'outgoing')),
        message TEXT,
        created_at TIMESTAMPTZ DEFAULT NOW()
    );

    CREATE TABLE IF NOT EXISTS logs (
        id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
        action_type TEXT NOT NULL,
        message TEXT,
        user_phone TEXT,
        channel TEXT,
        created_at TIMESTAMPTZ DEFAULT NOW()
    );

    CREATE TABLE IF NOT EXISTS debug_logs (
        id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
        error_source TEXT NOT NULL,
        error_message TEXT,
        raw_payload TEXT,
        created_at TIMESTAMPTZ DEFAULT NOW()
    );
    
    CREATE TABLE IF NOT EXISTS reminders (
        id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
        customer_id UUID,
        reminder_type TEXT DEFAULT 'payment',
        message TEXT,
        scheduled_for TIMESTAMPTZ,
        status TEXT DEFAULT 'pending',
        repeat_interval_days INTEGER DEFAULT 7,
        next_run TIMESTAMPTZ,
        created_at TIMESTAMPTZ DEFAULT NOW()
    );
    """
    
    # Try using sqlalchemy if available (common in fastapi)
    try:
        from sqlalchemy import create_engine, text
        if not DATABASE_URL:
            print("❌ DATABASE_URL not found in .env")
            return
            
        engine = create_engine(DATABASE_URL)
        with engine.connect() as conn:
            conn.execute(text(sql))
            conn.commit()
        print("✅ Tables created successfully via SQLAlchemy")
        return
    except ImportError:
        print("⚠️ SQLAlchemy not found.")
    except Exception as e:
        print(f"❌ SQLAlchemy failed: {e}")

    # Fallback: psycopg2
    try:
        import psycopg2
        conn = psycopg2.connect(DATABASE_URL)
        cur = conn.cursor()
        cur.execute(sql)
        conn.commit()
        cur.close()
        conn.close()
        print("✅ Tables created successfully via Psycopg2")
    except ImportError:
        print("⚠️ Psycopg2 not found.")
    except Exception as e:
        print(f"❌ Psycopg2 failed: {e}")

if __name__ == "__main__":
    apply_schema()
