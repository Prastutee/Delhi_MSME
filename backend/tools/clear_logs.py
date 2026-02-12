"""
Log Cleanup Utility
Prunes logs from the 'logs' table in Supabase.
"""
import sys
import os
from datetime import datetime, timedelta

# Add parent to path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from db import get_db

def clear_logs(days_to_keep: int = 30):
    print("\n" + "="*50)
    print("🧹 LOG CLEANUP UTILITY")
    print("="*50)
    
    try:
        db = get_db()
        cutoff_date = (datetime.utcnow() - timedelta(days=days_to_keep)).isoformat()
        
        print(f"   Removing logs older than: {cutoff_date} ({days_to_keep} days)")
        
        # Delete logs older than cutoff
        # Note: Supabase delete requires a where clause
        response = db.table("logs").delete().lt("created_at", cutoff_date).execute()
        
        # Supabase-py 'execute' usually returns a response object with .data
        # Depending on version, it might return count if count='exact' is passed
        # But delete().execute() returns the deleted rows in .data usually
        
        deleted_count = len(response.data) if response.data else 0
        
        print(f"   ✅ Deleted {deleted_count} old logs.")
        print("="*50 + "\n")
        
    except Exception as e:
        print(f"❌ Error clearing logs: {e}")

if __name__ == "__main__":
    import argparse
    parser = argparse.ArgumentParser(description="Clean up old logs")
    parser.add_argument("--days", type=int, default=30, help="Days of logs to keep (default: 30)")
    args = parser.parse_args()
    
    clear_logs(args.days)
