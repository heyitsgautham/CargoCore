import asyncio
import asyncpg
import bcrypt
import uuid

async def main():
    conn = await asyncpg.connect('postgresql://logistics_user:logistics_pass@localhost:5432/logistics_db')
    
    # 1. Get driver role id
    role_id = await conn.fetchval("SELECT id FROM roles WHERE name = 'driver'")
    if not role_id:
        print("Driver role not found! Inserting...")
        role_id = await conn.fetchval("INSERT INTO roles (name) VALUES ('driver') RETURNING id")
        
    # 2. Check if driver exists
    existing = await conn.fetchval("SELECT id FROM users WHERE email = 'driver@example.com'")
    if existing:
        print("Driver driver@example.com already exists.")
        return

    # 3. Hash password
    salt = bcrypt.gensalt()
    hashed = bcrypt.hashpw(b'StrongPass123', salt).decode('utf-8')
    
    # 4. Insert user
    user_id = str(uuid.uuid4())
    query = """
    INSERT INTO users (id, name, username, email, phone, role_id, password_hash, preferred_language, preferred_currency, default_payment_method)
    VALUES ($1, $2, $3, $4, $5, $6, $7, 'en', 'INR', 'Full Payment')
    RETURNING id
    """
    await conn.fetchval(query, user_id, 'Test Driver', 'testdriver', 'driver@example.com', '1234567890', role_id, hashed)
    print("Created driver@example.com with password StrongPass123")
    
    await conn.close()

asyncio.run(main())
