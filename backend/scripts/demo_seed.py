"""
Demo Seed Script for Bharat Biz-Agent
Run this before demo to populate test data
IDEMPOTENT - safe to run multiple times

FIXED: Proper dotenv loading and error handling
"""
import os
import sys
from pathlib import Path
from dotenv import load_dotenv

# Load environment from backend/.env
_backend_dir = Path(__file__).parent
load_dotenv(_backend_dir / ".env")

# Add backend to path
sys.path.insert(0, str(_backend_dir))

from supabase import create_client


def get_db():
    """Get Supabase client"""
    url = os.getenv("SUPABASE_URL")
    key = os.getenv("SUPABASE_KEY")
    
    if not url or not key:
        print("❌ SUPABASE_URL and SUPABASE_KEY must be set in backend/.env")
        print(f"   Looking at: {_backend_dir / '.env'}")
        sys.exit(1)
    
    return create_client(url, key)


def check_tables_exist(db) -> bool:
    """Check if required tables exist"""
    required_tables = ["customers", "inventory", "transactions", "logs", "pending_actions"]
    
    for table in required_tables:
        try:
            db.table(table).select("id").limit(1).execute()
        except Exception as e:
            if "PGRST205" in str(e):
                return False
            raise
    return True


def upsert_customer(db, name: str, phone: str):
    """Insert or update customer"""
    try:
        existing = db.table("customers").select("*").eq("phone", phone).execute()
        if existing.data:
            db.table("customers").update({"name": name}).eq("phone", phone).execute()
            print(f"  ✓ Updated customer: {name}")
        else:
            db.table("customers").insert({"name": name, "phone": phone}).execute()
            print(f"  ✓ Created customer: {name}")
    except Exception as e:
        print(f"  ⚠ Customer {name}: {str(e)[:50]}")


def upsert_inventory(db, item_name: str, quantity: int, price: float, threshold: int, unit: str = "pcs"):
    """Insert or update inventory item"""
    try:
        existing = db.table("inventory").select("*").eq("item_name", item_name).execute()
        data = {
            "item_name": item_name,
            "quantity": quantity,
            "price": price,
            "low_stock_threshold": threshold,
            "unit": unit
        }
        if existing.data:
            db.table("inventory").update(data).eq("item_name", item_name).execute()
            print(f"  ✓ Updated: {item_name} (qty={quantity}, ₹{price})")
        else:
            db.table("inventory").insert(data).execute()
            print(f"  ✓ Created: {item_name} (qty={quantity}, ₹{price})")
    except Exception as e:
        print(f"  ⚠ Inventory {item_name}: {str(e)[:50]}")


def upsert_supplier(db, item_name: str, supplier_name: str, phone: str):
    """Insert or update supplier"""
    try:
        existing = db.table("suppliers").select("*").eq("item_name", item_name).execute()
        data = {
            "item_name": item_name,
            "supplier_name": supplier_name,
            "phone": phone
        }
        if existing.data:
            db.table("suppliers").update(data).eq("item_name", item_name).execute()
            print(f"  ✓ Updated supplier: {item_name} → {supplier_name}")
        else:
            db.table("suppliers").insert(data).execute()
            print(f"  ✓ Created supplier: {item_name} → {supplier_name}")
    except Exception as e:
        print(f"  ⚠ Supplier {item_name}: {str(e)[:50]}")


def clear_transactions(db):
    """Clear old transactions for clean demo"""
    try:
        # Delete all records (Supabase requires a filter, so we use neq with impossible UUID)
        db.table("transactions").delete().neq("id", "00000000-0000-0000-0000-000000000000").execute()
        db.table("pending_actions").delete().neq("id", "00000000-0000-0000-0000-000000000000").execute()
        print("  ✓ Cleared previous transactions")
    except Exception as e:
        print(f"  ⚠ Clear transactions: {str(e)[:50]}")


def seed_demo_data():
    """Main seeding function"""
    print("\n" + "="*50)
    print("🌱 BHARAT BIZ-AGENT - DEMO SEED")
    print("="*50 + "\n")
    
    db = get_db()
    
    # Check if tables exist
    print("🔍 Checking database schema...")
    if not check_tables_exist(db):
        print("\n" + "="*50)
        print("❌ DATABASE TABLES NOT FOUND!")
        print("="*50)
        print("\nYou need to run schema.sql in Supabase SQL Editor first.")
        print("\n📋 Steps:")
        print("   1. Open Supabase Dashboard → SQL Editor")
        print("   2. Copy contents of backend/schema.sql")
        print("   3. Paste and click 'Run'")
        print("   4. Run this script again")
        print("\n" + "="*50)
        sys.exit(1)
    
    print("  ✓ All tables exist\n")
    
    # 1. Customers
    print("👥 Seeding Customers...")
    upsert_customer(db, "Rakesh", "demo_rakesh_001")
    upsert_customer(db, "Mohan", "demo_mohan_002")
    upsert_customer(db, "Sharma Ji", "demo_sharma_003")
    
    # 2. Inventory
    print("\n📦 Seeding Inventory...")
    upsert_inventory(db, "Milk", quantity=10, price=30, threshold=3, unit="packet")
    upsert_inventory(db, "Parle-G", quantity=25, price=10, threshold=5, unit="pkt")
    upsert_inventory(db, "Rice", quantity=5, price=60, threshold=2, unit="kg")
    upsert_inventory(db, "Maggi", quantity=50, price=14, threshold=10, unit="pkt")
    upsert_inventory(db, "Tata Salt", quantity=20, price=28, threshold=5, unit="pcs")
    
    # 3. Suppliers
    print("\n🏭 Seeding Suppliers...")
    upsert_supplier(db, "Milk", "Sharma Wholesale", "+917085486346")
    upsert_supplier(db, "Parle-G", "Gupta Distributors", "+919387788002")
    upsert_supplier(db, "Rice", "Assam Grain Market", "+917896621746")
    
    # 4. Clear old transactions
    print("\n🧹 Cleaning up...")
    clear_transactions(db)
    
    print("\n" + "="*50)
    print("✅ DEMO READY!")
    print("="*50)
    print("\n🚀 Start bot: python backend/tools/telegram_bot.py")
    print("\n📝 Demo Scenarios:")
    print("   1. 'Rakesh ne 3 doodh udhaar liya' → Credit Sale")
    print("   2. 'Rakesh ne 50 rupaye de diye' → Payment")
    print("   3. 'Milk stock kitna hai?' → Inventory Query")
    print()


if __name__ == "__main__":
    seed_demo_data()
