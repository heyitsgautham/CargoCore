import asyncio

from redis.asyncio import from_url


async def main():
    r = from_url('redis://localhost:6379/0', decode_responses=True)
    await r.set('test_key', '123456')
    print(await r.get('test_key'))
asyncio.run(main())
