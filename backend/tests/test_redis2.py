import asyncio

from redis.asyncio import from_url


async def main():
    r = from_url('redis://localhost:6379/0', decode_responses=True)
    print(await r.keys('*'))
asyncio.run(main())
