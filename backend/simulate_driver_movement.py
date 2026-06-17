"""
Simulate a driver moving around Mumbai
Creates realistic GPS trail for testing real-time tracking
"""
import asyncio
import sys
import random
from sqlalchemy import select

sys.path.insert(0, ".")

from app.database import AsyncSessionLocal as SessionLocal
from app.models.user import User
from app.models.logistics import LogisticsDriverProfile


async def simulate_driver_movement():
    print("🚗 Starting driver movement simulation...\n")

    async with SessionLocal() as db:
        # Get test driver
        result = await db.execute(
            select(User, LogisticsDriverProfile)
            .join(LogisticsDriverProfile, User.id == LogisticsDriverProfile.user_id)
            .where(User.email == "driver1@gmail.com")
        )
        row = result.first()

        if not row:
            print("❌ Test driver not found. Run test_tracking_api.py first.")
            return

        driver, profile = row
        print(f"✅ Found driver: {driver.name}")

        # Route: Andheri → Bandra → Lower Parel (Mumbai)
        route = [
            (19.1136, 72.8697, "Starting at Andheri West"),
            (19.1200, 72.8750, "Moving towards Jogeshwari"),
            (19.1300, 72.8800, "Approaching Vile Parle"),
            (19.1350, 72.8850, "Near Santa Cruz"),
            (19.1400, 72.8900, "Entering Khar"),
            (19.0650, 72.8350, "Reached Bandra West"),
            (19.0200, 72.8400, "Moving to Mahim"),
            (19.0008, 72.8295, "Arrived at Lower Parel"),
        ]

        profile.status = "In-Transit"
        await db.commit()

        print(
            "\n🗺️  Driver route: Andheri West → Bandra West → Lower Parel"
        )
        print("⏱️  Updates every 5 seconds\n")
        print("📡 Test the tracking endpoint while this runs:\n")
        print(
            "   curl http://127.0.0.1:8000/api/v1/tracking/drivers \\"
        )
        print("     -H 'Authorization: Bearer YOUR_TOKEN_HERE'\n")

        for i, (lat, lng, description) in enumerate(route, 1):
            # Add small random variations for realism
            lat_jitter = random.uniform(-0.0005, 0.0005)
            lng_jitter = random.uniform(-0.0005, 0.0005)

            final_lat = round(lat + lat_jitter, 6)
            final_lng = round(lng + lng_jitter, 6)

            # Update location
            profile.current_location = f"{final_lat},{final_lng}"
            await db.commit()

            print(
                f"📍 Step {i}/{len(route)}: {description}"
            )
            print(f"   GPS: {final_lat}, {final_lng}")

            if i < len(route):
                await asyncio.sleep(5)

        # Mark as completed
        profile.status = "On-Duty"
        await db.commit()

        print("\n✅ Simulation complete!")
        print(
            f"🏁 Final position: {profile.current_location} (Lower Parel)"
        )


if __name__ == "__main__":
    try:
        asyncio.run(simulate_driver_movement())
    except KeyboardInterrupt:
        print("\n\n⏹️  Simulation stopped by user")
