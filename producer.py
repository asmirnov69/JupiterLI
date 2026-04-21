import asyncio
import random
import redis

REDIS_URL = "redis://localhost"

async def producer():
    r = redis.from_url(REDIS_URL, decode_responses=True)

    while True:
        await asyncio.sleep(2.5)

        new_val = random.randint(1, 10)

        # Push to a Redis list
        r.lpush("chart:data", new_val)

        # Optional: limit list size
        r.ltrim("chart:data", 0, 100)

        print("Produced:", new_val)

if __name__ == "__main__":
    asyncio.run(producer())
