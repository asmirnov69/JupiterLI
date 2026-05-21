import asyncio
import json
import traceback

import zmq
import zmq.asyncio

ZMQ_SUB_ENDPOINT = "tcp://localhost:5555"


class KeySubscriber:
    def __init__(self, handler):
        self.buffer = []
        self.handler = handler


class ZmqLoop:
    def __init__(self):
        self.ctx = zmq.asyncio.Context.instance()
        self.socket = self.ctx.socket(zmq.SUB)
        self.socket.connect(ZMQ_SUB_ENDPOINT)
        self.subscribers = {}  # key -> KeySubscriber
        self.batch_is_done = asyncio.Event()

    async def flush(self):
        # No central store to clear; just drop any pending data in local buffers.
        for sub in self.subscribers.values():
            sub.buffer = []

    def subscribe(self, key, message_handler):
        if key in self.subscribers:
            return
        self.subscribers[key] = KeySubscriber(message_handler)
        self.socket.setsockopt(zmq.SUBSCRIBE, key.encode("utf-8"))

    async def loop(self):
        try:
            await self.zmq_update_loop_body()
        except asyncio.CancelledError as ce:
            print("exception in ZmqLoop::loop: Cancelled")
            traceback.print_exception(type(ce), ce, ce.__traceback__)
            self.socket.close(0)
        except Exception as e:
            print("exception in ZmqLoop::loop: Stopping loop due to:", e)
            traceback.print_exception(type(e), e, e.__traceback__)

    async def zmq_update_loop_body(self):
        while True:
            await asyncio.sleep(0.5)

            if not self.subscribers:
                continue

            got_any = False
            while True:
                try:
                    topic_bytes, payload_bytes = await self.socket.recv_multipart(flags=zmq.NOBLOCK)
                except zmq.Again:
                    break
                topic = topic_bytes.decode("utf-8")
                sub = self.subscribers.get(topic)
                if sub is None:
                    continue
                msg = json.loads(payload_bytes.decode("utf-8"))
                # Downstream curve code does float(it['value']) / float(it['timestamp']);
                # stringify values to match what redis returned with decode_responses=True.
                sub.buffer.append({k: str(v) for k, v in msg.items()})
                got_any = True

            if not got_any:
                continue

            for key, s in self.subscribers.items():
                print("len(stream_items):", len(s.buffer), key)
                s.handler(key, s.buffer)
                s.buffer = []

            self.batch_is_done.set()
