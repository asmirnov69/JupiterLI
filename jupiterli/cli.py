import asyncio, uuid
from nicegui import ui
from jupiterli.redis_utils import RedisLoop
from jupiterli.plotter_loop import PlotterLoop
from jupiterli.config import load_config


def setup_page():
    rl = RedisLoop()
    pl = PlotterLoop(rl)

    load_config(pl, "examples/producer.ttl")

    loop = asyncio.get_event_loop()
    loop.create_task(pl.loop())

    redis_task = loop.create_task(rl.loop())
    redis_task.set_name(f"redis-task--{uuid.uuid4().hex[:8]}")
    ui.context.client.on_disconnect(redis_task.cancel)


def main():
    ui.page('/')(setup_page)
    ui.run(reload=False)


if __name__ in {"__main__", "__mp_main__"}:
    main()
