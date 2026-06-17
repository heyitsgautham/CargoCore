import asyncio
import asyncpg
import bcrypt

async def main():
    conn = await asyncpg.connect('postgresql://logistics_user:logistics_pass@localhost:5432/logistics_db')
    
    # Hash password "12345678"
    salt = bcrypt.gensalt()
    hashed = bcrypt.hashpw(b'12345678', salt).decode('utf-8')
    
    # Update drivers
    query = """
    UPDATE users SET password_hash = $1 WHERE email IN ('driver1@gmail.com', 'driver2@gmail.com')
    """
    await conn.execute(query, hashed)
    print("Passwords for driver1 and driver2 have been reset to 12345678.")
    
    await conn.close()

asyncio.run(main())
