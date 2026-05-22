import asyncio, json
import redis.asyncio
import traceback, inspect

class KeySubscriber:
    def __init__(self, handler):
        self.buffer = []
        self.handler = handler

class RedisLoop:
    def __init__(self, app):
        self.r = redis.asyncio.from_url("redis://localhost", decode_responses=True)
        self.subscribers = {} # key -> KeySubscriber
        self.last_id = "$" # we start from new message, old ones are in db
        self.batch_is_done = asyncio.Event()

        self.series_ids_d = app.series_ids_d
        print(self.series_ids_d)
        
    async def flush(self):
        await self.r.flushdb()
        
    def subscribe(self, key, message_handler):
        if key in self.subscribers:
            return
        new_subscriber = KeySubscriber(message_handler)
        self.subscribers[key] = new_subscriber

    async def loop(self):
        try:
            await self.redis_update_loop_body()
        except Exception as e:
            print("exception in RedisLoop::loop: Stopping loop due to:", e)
            traceback.print_exception(type(e), e, e.__traceback__)
        except asyncio.CancelledError as ce:
            print("exception in RedisLoop::loop: Cancelled")
            traceback.print_exception(type(ce), ce, ce.__traceback__)

    async def redis_update_loop_body(self):
        running_env = True
        while running_env:
            await asyncio.sleep(0.5)
            
            all_stream_data = await self.r.xread({'telemetry': self.last_id}, block = 0)

            print(f"xread returned {len(all_stream_data) if all_stream_data else 0} streams")
            if not all_stream_data:
                continue

            for stream_data in all_stream_data:
                stream_name, stream_items = stream_data
                if stream_name != 'telemetry':
                    continue
                l_stream_items = [x for x in stream_items]
                print("len(stream_items):", len(l_stream_items), stream_name)
                self.last_id = l_stream_items[-1][0]
                #print(l_stream_items)
                for _, stream_item_data in l_stream_items:                    
                    stream_item = json.loads(stream_item_data.get('data'))
                    print(stream_item)
                    series_id = stream_item.get("series_id")                    
                    key = self.series_ids_d.get(series_id)
                    print("KEY:", key, series_id, self.series_ids_d)
                    subscriber = self.subscribers.get(key)
                    if subscriber is None:
                        continue
                    subscriber.buffer.append(stream_item)

            for key, s in self.subscribers.items():
                print("key", key, s.buffer)
                s.handler(key, s.buffer)
                s.buffer = []

            self.batch_is_done.set()
