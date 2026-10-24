"""
Test script to verify attendance tracking is working correctly.

This script will:
1. Connect to the database
2. Check users' last_login timestamps
3. Display who would be marked as "present" based on today's date
"""
import asyncio
import sys
from datetime import UTC, datetime
from pathlib import Path

from sqlalchemy import select

# Add backend directory to path
backend_path = Path(__file__).parent / "backend"
sys.path.insert(0, str(backend_path))

from app.database import AsyncSessionLocal
from app.models.user import User


async def check_attendance():
    async with AsyncSessionLocal() as session:
        # Get all users
        result = await session.execute(
            select(User).where(User.is_active == True)
        )
        users = result.scalars().all()
        
        # Get today's date in YYYY-MM-DD format
        today_str = datetime.now(UTC).date().isoformat()
        
        print(f"\n{'='*80}")
        print(f"ATTENDANCE REPORT - {today_str}")
        print(f"{'='*80}\n")
        
        present_count = 0
        absent_count = 0
        
        for user in users:
            if user.last_login:
                # Check if last_login date matches today
                last_login_str = user.last_login.date().isoformat()
                is_present = last_login_str == today_str
                
                status = "✓ PRESENT" if is_present else "✗ ABSENT"
                if is_present:
                    present_count += 1
                else:
                    absent_count += 1
                
                print(f"{status:12} | {user.name:30} | {user.email:35} | Last Login: {user.last_login}")
            else:
                absent_count += 1
                print(f"{'✗ ABSENT':12} | {user.name:30} | {user.email:35} | Last Login: Never")
        
        print(f"\n{'='*80}")
        print(f"SUMMARY: {present_count} Present | {absent_count} Absent | {present_count + absent_count} Total")
        print(f"{'='*80}\n")
        
        if present_count == 0:
            print("⚠️  NOTE: No users have logged in today.")
            print("   To test attendance, try logging in with a user account.")
            print("   After login, run this script again to see them marked as PRESENT.\n")


if __name__ == "__main__":
    asyncio.run(check_attendance())
