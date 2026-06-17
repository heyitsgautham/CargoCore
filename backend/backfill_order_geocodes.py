"""
Backfill delivery coordinates for existing orders using geocoding.
Run this script once to update orders that don't have lat/lng set.

Usage:
    cd backend
    python backfill_order_geocodes.py
"""

import asyncio
import sys
import time

# Add parent directory to path for imports
sys.path.insert(0, '.')

import psycopg2
import httpx

NOMINATIM_URL = "https://nominatim.openstreetmap.org/search"
USER_AGENT = "CargoCore-Logistics/1.0"

# Database connection
DB_CONFIG = {
    'host': 'localhost',
    'database': 'logistics_db',
    'user': 'logistics_user',
    'password': 'logistics_pass'
}


def geocode_address_sync(address: str) -> tuple[float, float] | None:
    """Synchronous geocoding using Nominatim."""
    if not address or len(address.strip()) < 5:
        return None
    
    try:
        response = httpx.get(
            NOMINATIM_URL,
            params={
                "q": address,
                "format": "json",
                "limit": 1,
            },
            headers={"User-Agent": USER_AGENT},
            timeout=10.0
        )
        
        if response.status_code != 200:
            print(f"  ⚠ API returned {response.status_code}")
            return None
        
        results = response.json()
        
        if not results:
            print(f"  ⚠ No results found")
            return None
        
        lat = float(results[0]["lat"])
        lng = float(results[0]["lon"])
        return (lat, lng)
        
    except Exception as e:
        print(f"  ✗ Error: {e}")
        return None


def backfill_orders():
    """Backfill delivery coordinates for all orders missing them."""
    conn = psycopg2.connect(**DB_CONFIG)
    cur = conn.cursor()
    
    # Find orders without coordinates but with delivery address
    cur.execute("""
        SELECT id, delivery_addr 
        FROM orders 
        WHERE delivery_addr IS NOT NULL 
          AND delivery_addr != ''
          AND (delivery_lat IS NULL OR delivery_lng IS NULL)
    """)
    
    orders = cur.fetchall()
    total = len(orders)
    
    print(f"\n📍 Found {total} orders needing geocoding\n")
    
    if total == 0:
        print("✅ All orders already have coordinates!")
        conn.close()
        return
    
    updated = 0
    failed = 0
    
    for i, (order_id, delivery_addr) in enumerate(orders, 1):
        print(f"[{i}/{total}] Order {str(order_id)[:8]}...")
        print(f"  Address: {delivery_addr[:60]}...")
        
        # Rate limit: 1 request per second for Nominatim
        time.sleep(1.1)
        
        coords = geocode_address_sync(delivery_addr)
        
        if coords:
            lat, lng = coords
            cur.execute(
                "UPDATE orders SET delivery_lat = %s, delivery_lng = %s WHERE id = %s",
                (lat, lng, order_id)
            )
            conn.commit()
            print(f"  ✓ Updated: ({lat:.6f}, {lng:.6f})")
            updated += 1
        else:
            failed += 1
    
    conn.close()
    
    print(f"\n{'='*50}")
    print(f"📊 Summary:")
    print(f"   ✓ Updated: {updated}")
    print(f"   ✗ Failed:  {failed}")
    print(f"   Total:     {total}")
    print(f"{'='*50}\n")


if __name__ == "__main__":
    print("\n🚀 Starting order geocoding backfill...\n")
    backfill_orders()
    print("✅ Done!")
