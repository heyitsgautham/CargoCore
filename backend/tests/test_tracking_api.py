"""
Test the real-time tracking API endpoints
"""
import asyncio
import sys

from sqlalchemy import select

sys.path.insert(0, ".")

from app.database import AsyncSessionLocal as SessionLocal
from app.models.logistics import LogisticsDriverProfile
from app.models.user import User


async def test_tracking():
    print("🧪 Testing Tracking API\n")

    async with SessionLocal() as db:
        # Find a driver with location
        result = await db.execute(
            select(User, LogisticsDriverProfile)
            .join(LogisticsDriverProfile, User.id == LogisticsDriverProfile.user_id)
            .where(LogisticsDriverProfile.current_location.isnot(None))
            .limit(1)
        )
        row = result.first()

        if not row:
            print("⚠️  No drivers with location found")
            print("💡 Creating test driver with location...")

            # Get or create test driver
            driver_result = await db.execute(
                select(User).where(User.email == "driver1@gmail.com")
            )
            driver = driver_result.scalar_one_or_none()

            if driver:
                # Update their profile with a location
                profile_result = await db.execute(
                    select(LogisticsDriverProfile).where(
                        LogisticsDriverProfile.user_id == driver.id
                    )
                )
                profile = profile_result.scalar_one_or_none()

                if not profile:
                    # Create profile if doesn't exist
                    profile = LogisticsDriverProfile(
                        user_id=driver.id,
                        license_number="TEST-LIC-123",
                        status="On-Duty",
                        current_location="19.1136,72.8697",  # Andheri, Mumbai
                    )
                    db.add(profile)
                else:
                    profile.current_location = "19.1136,72.8697"
                    profile.status = "On-Duty"
                    db.add(profile)

                await db.commit()
                print("✅ Set test driver location: 19.1136, 72.8697")
            else:
                print("❌ Test driver not found. Run create_test_order.py first.")
                return

        else:
            driver, profile = row
            print(
                f"✅ Found driver: {driver.name} at {profile.current_location}"
            )

    print("\n📍 Now test the API endpoints:")
    print("\n1. Get All Active Drivers:")
    print("   curl -X GET http://127.0.0.1:8000/api/v1/tracking/drivers \\")
    print("     -H 'Authorization: Bearer YOUR_TOKEN_HERE'")

    print("\n2. Login to get token:")
    print("   curl -X POST http://127.0.0.1:8000/api/v1/auth/login \\")
    print("     -H 'Content-Type: application/json' \\")
    print("     -d '{\"email\":\"driver.test@cargocore.com\",\"password\":\"Test@123\"}'")

    print("\n3. Or use logistic manager:")
    print("   curl -X POST http://127.0.0.1:8000/api/v1/auth/login \\")
    print("     -H 'Content-Type: application/json' \\")
    print(
        "     -d '{\"email\":\"logistic.manager@cargocore.com\",\"password\":\"Admin@123\"}'"
    )

    print("\n✅ Test setup complete!")
    print("🔥 Backend should be running on http://127.0.0.1:8000")
    print("📖 API docs: http://127.0.0.1:8000/docs")


if __name__ == "__main__":
    asyncio.run(test_tracking())
