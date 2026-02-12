"""
Seed Demo Data
Adds sample customers, inventory, transactions, and logs to Supabase
"""
import asyncio
import sys
import os
from datetime import datetime, timedelta
import random

# Add parent to path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from db import get_db, log_event

async def seed_data():
    print("\n" + "="*50)
    print("🌱 SEEDING DEMO DATA")
    print("="*50)
    
    db = get_db()
    
    # 1. Customers
    customers = [
        {"name": "Rakesh Kumar", "phone": "9876543210"},
        {"name": "Amit Shah", "phone": "9988776655"},
        {"name": "Priya Singh", "phone": "9123456789"},
        {"name": "Rahul Gandhi", "phone": "9000000001"},
        {"name": "Sita Ram", "phone": "8887776665"},
        {"name": "Prabin Kumar", "phone": "9998887776"},
        {"name": "Sharma Ji", "phone": "8889990001"}
    ]
    
    print("   Adding customers...")
    for c in customers:
        try:
            db.table("customers").insert(c).execute()
        except:
            pass  # Ignore duplicates
            
    # Get customer IDs
    cust_rows = db.table("customers").select("id, name").execute().data
    
    # 2. Inventory
    inventory = [
        {"item_name": "Amul Milk", "quantity": 50, "unit": "pkt", "price": 34, "low_stock_threshold": 10},
        {"item_name": "Parle-G", "quantity": 100, "unit": "pkt", "price": 5, "low_stock_threshold": 20},
        {"item_name": "Tata Salt", "quantity": 5, "unit": "kg", "price": 28, "low_stock_threshold": 10},
        {"item_name": "Atta 5kg", "quantity": 2, "unit": "bag", "price": 250, "low_stock_threshold": 5},
        {"item_name": "Maggi", "quantity": 40, "unit": "pkt", "price": 14, "low_stock_threshold": 15},
        {"item_name": "Sugar", "quantity": 30, "unit": "kg", "price": 42, "low_stock_threshold": 10},
        {"item_name": "Rice (Basmati)", "quantity": 25, "unit": "kg", "price": 120, "low_stock_threshold": 5},
        {"item_name": "Mustard Oil", "quantity": 15, "unit": "ltr", "price": 160, "low_stock_threshold": 5},
        {"item_name": "Doodh (Loose)", "quantity": 10, "unit": "ltr", "price": 60, "low_stock_threshold": 2},
    ]
    
    print("   Adding inventory...")
    for i in inventory:
        try:
            db.table("inventory").insert(i).execute()
        except:
            pass

    # Get inventory IDs
    inv_rows = db.table("inventory").select("id, item_name, price").execute().data
    
    # 3. Transactions & Logs
    print("   Adding transactions & logs...")
    
    actions = ["sale_paid", "sale_credit", "payment"]
    
    for _ in range(20):
        action = random.choice(actions)
        cust = random.choice(cust_rows)
        item = random.choice(inv_rows)
        qty = random.randint(1, 5)
        
        if action == "sale_paid":
            amount = item["price"] * qty
            db.table("transactions").insert({
                "customer_id": cust["id"],
                "amount": amount,
                "type": "sale_paid",
                "description": f"{item['item_name']} x{qty} (cash)"
            }).execute()
            log_event("web_action", f"Sale: {cust['name']} bought {item['item_name']} x{qty}", channel="dashboard")
            
        elif action == "sale_credit":
            amount = item["price"] * qty
            db.table("transactions").insert({
                "customer_id": cust["id"],
                "amount": amount,
                "type": "sale_credit",
                "description": f"{item['item_name']} x{qty} (credit)"
            }).execute()
            log_event("web_action", f"Credit: {cust['name']} took {item['item_name']} x{qty} udhaar", channel="dashboard")
            
        elif action == "payment":
            amount = random.randint(100, 1000)
            db.table("transactions").insert({
                "customer_id": cust["id"],
                "amount": amount,
                "type": "payment",
                "description": f"Payment received: ₹{amount}"
            }).execute()
            log_event("web_action", f"Payment: {cust['name']} paid ₹{amount}", channel="dashboard")

    # 4. Reminders (Explicit Seeding)
    print("   Adding reminders...")
    for _ in range(5):
        cust = random.choice(cust_rows)
        days_later = random.randint(1, 7)
        db.table("reminders").insert({
            "customer_id": cust["id"],
            "reminder_type": "payment",
            "message": f"Payment reminder for {cust['name']}",
            "scheduled_for": (datetime.now() + timedelta(days=days_later)).isoformat(),
            "next_run": (datetime.now() + timedelta(days=days_later)).isoformat(),
            "repeat_interval_days": 7,
            "status": "pending"
        }).execute()
        
    # 5. Logs (Explicit Seeding for Golden Test)
    print("   Adding sample logs...")
    logs = [
        {"action_type": "sale_credit", "message": "Credit: Rakesh Kumar ₹180", "channel": "dashboard", "user_phone": "dashboard_user"},
        {"action_type": "inventory_update", "message": "Purchase: Amul Milk x50", "channel": "dashboard", "user_phone": "dashboard_user"},
        {"action_type": "reminder_scheduled", "message": "Sent autonomous reminder to 9876543210", "channel": "reminder_runner", "user_phone": None},
        {"action_type": "payment_received", "message": "Received ₹500 from Amit Shah", "channel": "dashboard", "user_phone": "dashboard_user"},
        {"action_type": "error", "message": "Execution error: Payment gateway timeout", "channel": "system", "user_phone": None}
    ]
    
    for log in logs:
        try:
            db.table("logs").insert(log).execute()
        except:
            pass

    print("\n✅ Seed data added successfully!")

if __name__ == "__main__":
    asyncio.run(seed_data())
