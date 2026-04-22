# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

**pyobserve** is a real-time data visualization framework that combines Redis Streams (data transport) with NiceGUI + Plotly (web dashboard). Data producers publish to Redis Streams; the UI polls for new messages and updates live charts in the browser.

## Installation and Running

```bash
# Install the package (from the repo root)
pip install -e .

# Start a Redis instance (required before running anything)
redis-server

# In one terminal — run the test data producer (publishes to Redis every 2.5s)
python examples/producer.py

# In another terminal — run the dashboard (serves on http://localhost:8080)
pyobserve
```

There are no tests and no linter config.

## Architecture

The package lives in `pyobserve/` with three modules:

### `pyobserve/redis_utils.py` — Stream Consumption
`RedisLoop` polls Redis Streams every 0.5s using `xread()`. Callers register stream keys with handlers via `subscribe(key, handler)`. After each polling cycle, all handlers are called with their buffered messages, then `batch_is_done` (`asyncio.Event`) is set to signal the UI layer. `KeySubscriber` is a small dataclass bundling a buffer and its handler.

### `pyobserve/cli.py` — UI and Visualization (entry point: `pyobserve`)
`PlotterLoop` owns a list of `Plot` objects and waits on `batch_is_done`. When triggered, it calls `fig.update()` on every plot to push data to the browser.

Plot types (`Histogram`, `Scatter`, `TimeseriesScatter`) all wrap a Plotly figure and expose an `append_curve(name, x, y)` method. They use `uirevision='constant'` so Plotly doesn't reset zoom/pan on each update.

Startup sequence in `main()`:
1. Register NiceGUI client-connect handler (waits for a browser connection before starting Redis polling)
2. Create `RedisLoop` and `PlotterLoop`, wire up subscriptions
3. Start `PlotterLoop.loop()` as a background `asyncio` task
4. Start `RedisLoop.loop()` (main async task)
5. `ui.run()` launches the NiceGUI server

### `examples/producer.py` — Synthetic Data Source
Publishes random float values to Redis Streams `data1` and `data2` every 2.5s using `xadd`. Streams are capped at 10,000 entries via `maxlen`. Run directly with `python examples/producer.py`.

## Key Design Decisions

- **Batch signal**: `RedisLoop` fires one `asyncio.Event` after processing all streams per cycle, so the UI updates once per polling interval rather than once per message.
- **Incremental reads**: `RedisLoop` tracks `last_id` per stream to fetch only new messages on each `xread` call.
- **Client-gated start**: Redis polling doesn't begin until a browser client connects (`on_connect` event), avoiding wasted polling when nobody is watching.
- **Redis URL**: Hardcoded as `"redis://localhost"` in both `producer.py` and `redis_utils.py` — change both if using a remote Redis instance.

## Known Issue

The current HEAD commit (`94dc2fa`) notes "problem behaviour during append" — there is a suspected bug in how chart data is appended during live updates.
