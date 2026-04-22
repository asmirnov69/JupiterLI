import asyncio
import redis.asyncio
import traceback, inspect

class KeySubscriber:
    def __init__(self, handler):
        self.buffer = []
        self.handler = handler

class RedisLoop:
    def __init__(self):
        self.r = redis.asyncio.from_url("redis://localhost", decode_responses=True)
        self.subscribers = {} # key -> KeySubscriber
        self.last_ids = {} # key -> last_id
        self.id_segments = {} # key -> (begin_id, end_id)
        self.batch_is_done = asyncio.Event()

    def subscribe(self, key, message_handler):
        if key in self.subscribers:
            return
        new_subscriber = KeySubscriber(message_handler)
        self.subscribers[key] = new_subscriber
        self.last_ids[key] = "0-0"

    async def loop(self):
        try:
            await self.redis_update_loop_body()
        except Exception as e:
            print("exception in RedisLoop::loop: Stopping loop due to:", e)
            traceback.print_exception(type(e), e, e.__traceback__)
        except asyncio.CancelledError:
            print("exception in RedisLoop::loop: Cancelled")

    async def redis_update_loop_body(self):
        running_env = True
        while running_env:
            await asyncio.sleep(0.5)

            all_stream_data = await self.r.xread(self.last_ids, block = 0)

            print(f"xread returned {len(all_stream_data) if all_stream_data else 0} streams")
            if not all_stream_data:
                continue

            for stream_data in all_stream_data:
                stream_name, stream_items = stream_data
                key = stream_name
                subsciber = self.subscribers.get(key)
                if subsciber is None:
                    continue
                l_stream_items = [x for x in stream_items]
                last_id = l_stream_items[-1][0]
                self.last_ids[key] = last_id
                print("len(stream_items):", len(l_stream_items))
                subsciber.buffer.extend([x[1] for x in l_stream_items])

            for key, s in self.subscribers.items():
                s.handler(key, s.buffer)
                s.buffer = []

            self.batch_is_done.set()
