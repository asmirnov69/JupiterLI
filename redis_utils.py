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
        #assert(not key in self.subscribers)
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
            
            #ipdb.set_trace()
            #print("self.last_ids:", self.last_ids)
            all_stream_data = await self.r.xread(self.last_ids, block = 0)

            print(f"xread returned {len(all_stream_data) if all_stream_data else 0} streams")
            if not all_stream_data:
                continue
            
            for stream_data in all_stream_data:
                stream_name, stream_items = stream_data
                #print(stream_name)
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
            
if __name__ == "__main__":

    class Printer:
        def __init__(self):
            self.prices = []; self.qtys = []

        def handle(self, key, messages):
            if key.endswith(".price"):
                self.prices.extend(messages)
            elif key.endswith(".qty"):
                self.qtys.extend(messages)
            else:
                raise Exception("unexpected key: " + key)
            
        async def process_batch(self, rl):
            while True:
                await rl.batch_is_done.wait()
                rl.batch_is_done = asyncio.Event()
                print("prices:", self.prices[-5:]); self.prices.clear()
                print("qtys:", self.qtys[-5:]); self.qtys.clear()
                print("batch is done")
    
    async def test_redis_loop():
        print("starting test_redis_loop")
        rl = RedisLoop()
        printer = Printer()
        rl.subscribe("apple_market:trade.price", printer.handle)
        rl.subscribe("apple_market:trade.qty", printer.handle)
        asyncio.create_task(printer.process_batch(rl))
        await rl.loop()
        print("test_redis_loop before return")
        
    async def main():
        print("starting async main")
        t = asyncio.create_task(test_redis_loop())
        try:
            await t
            print("await t complete, going to sleep 3 sec")
            await asyncio.sleep(3)
        except asyncio.CancelledError:
            print("exception in main(): test_redis_loop cancelled")

        print("sleep in main() before return")
        await asyncio.sleep(3.0)
        print("main before return")

    print("starting __main__")
    asyncio.run(main())
    print("all done")
    
    
