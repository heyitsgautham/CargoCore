import asyncio
import asyncpg
import bcrypt

PIN = '1234'

async def main():
    conn = await asyncpg.connect('postgresql://logistics_user:logistics_pass@localhost:5432/logistics_db')

    hashed = bcrypt.hashpw(PIN.encode(), bcrypt.gensalt()).decode('utf-8')

    rows = await conn.fetch("""
        UPDATE users
        SET password_hash = $1
        FROM roles
        WHERE users.role_id = roles.id
          AND roles.name = 'DRIVER'
        RETURNING users.username, users.name, users.email
    """, hashed)

    if not rows:
        print("No driver accounts found in the database.")
    else:
        print(f"\nPIN reset to '{PIN}' for {len(rows)} driver(s):\n")
        print(f"{'Driver ID (username)':<25} {'Name':<25} {'Email'}")
        print("-" * 75)
        for r in rows:
            print(f"{r['username']:<25} {r['name']:<25} {r['email']}")
        print(f"\nDrivers log in with: Driver ID above + PIN: {PIN}")

    await conn.close()

asyncio.run(main())
