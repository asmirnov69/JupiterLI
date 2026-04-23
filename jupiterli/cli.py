import asyncio, os, pathlib, sys, uuid
from nicegui import ui, app
from jupiterli.redis_utils import RedisLoop
from jupiterli.plotter_loop import PlotterLoop
from jupiterli.config import load_config

TTL_PATH = "examples/producer.ttl"
PKG_DIR = pathlib.Path(__file__).parent


def setup_page():
    rl = RedisLoop()
    pl = PlotterLoop(rl)

    load_config(pl, TTL_PATH)

    loop = asyncio.get_event_loop()
    loop.create_task(pl.loop())

    redis_task = loop.create_task(rl.loop())
    redis_task.set_name(f"redis-task--{uuid.uuid4().hex[:8]}")
    ui.context.client.on_disconnect(redis_task.cancel)


def _watched_mtimes():
    paths = [TTL_PATH, *(str(p) for p in PKG_DIR.rglob("*.py"))]
    out = {}
    for path in paths:
        try:
            out[path] = os.stat(path).st_mtime
        except FileNotFoundError:
            pass
    return out


async def _watch_files():
    last = _watched_mtimes()
    while True:
        await asyncio.sleep(1.0)
        current = _watched_mtimes()
        for path, mtime in current.items():
            if path in last and mtime != last[path]:
                print(f"{path} changed, restarting...", flush=True)
                os.execv(sys.executable, [sys.executable, *sys.argv])
        last = current


def main():
    ui.page('/')(setup_page)
    app.on_startup(_watch_files)
    ui.run(reload=False)


if __name__ in {"__main__", "__mp_main__"}:
    main()
