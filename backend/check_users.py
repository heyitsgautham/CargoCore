import asyncio
from app.database import async_engine
from sqlalchemy import text

async def check():
    async with async_engine.connect() as conn:
        result = await conn.execute(text('SELECT email, name, created_at FROM users ORDER BY created_at DESC LIMIT 10'))
        print('Recent users in database:')
        rows = result.fetchall()
        if not rows:
            print('  (No users found)')
        for row in rows:
            print(f'  - {row[0]} | {row[1]} | created: {row[2]}')

asyncio.run(check())
