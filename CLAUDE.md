# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

**JupiterLI** is a real-time data visualization framework that combines ZeroMQ PUB/SUB (data transport) with NiceGUI + Plotly (web dashboard). Data producers publish to a ZeroMQ PUB socket; the UI subscribes to topics and updates live charts in the browser.

## Installation and Running

```bash
# Install the package (from the repo root)
pip install -e .

# In one terminal — run the test data producer (binds tcp://*:5555 and publishes every 0.25s)
python examples/producer.py

# In another terminal — run the dashboard (serves on http://localhost:8080)
jupiterli-backend examples/producer.ttl
```

There are no tests and no linter config.

## Architecture

The package lives in `jupiterli/`. The producer-facing API is in `jupiterli/__init__.py`; the dashboard backend lives in `jupiterli/backend/`.

### `jupiterli/__init__.py` — Producer API
Exposes `add_serial_point(key, value)` and `add_ts_point(key, ts, value)`. Both call `_get_pub_socket()`, which lazily creates a single `zmq.PUB` socket bound to `tcp://*:5555` (constant `ZMQ_PUB_ENDPOINT`) on first use, then publishes a two-frame message `[topic_bytes, json_bytes]` where `topic_bytes` is the stream key and `json_bytes` is the payload dict serialized as JSON. Binding is lazy so importing `jupiterli` from the backend does not open a socket.

### `jupiterli/backend/zmq_utils.py` — Stream Consumption
`ZmqLoop` owns a `zmq.asyncio.SUB` socket connected to `tcp://localhost:5555` (constant `ZMQ_SUB_ENDPOINT`). Callers register stream keys with handlers via `subscribe(key, handler)`, which also installs a `zmq.SUBSCRIBE` topic filter on the socket. The loop sleeps 0.5s per cycle, then drains all available messages with `recv_multipart(flags=NOBLOCK)` until `zmq.Again`. Payloads are JSON-decoded and stringified to match what `redis.from_url(..., decode_responses=True)` used to return (so downstream `float(it['value'])` calls keep working). If any messages arrived, each subscriber's handler is called with its buffered messages, the buffer is cleared, then `batch_is_done` (`asyncio.Event`) is set to signal the UI layer. `KeySubscriber` is a small dataclass bundling a buffer and its handler. `flush()` is a no-op buffer reset (there is no central store to clear).

### `jupiterli/backend/plots.py` — Plot Types
`Plot` wraps a NiceGUI `ui.plotly` element and owns a list of curve objects. It exposes `add_scatter`, `add_timeseries_scatter`, and `add_histogram` methods, each of which creates the corresponding curve object, registers a ZMQ topic subscription via `pl.rl.subscribe(key, ...)`, and tracks the curve in `PlotterLoop`'s `scatters` / `histograms` dicts.

Curve classes `Histogram`, `Scatter`, `TimeseriesScatter` each hold an internal `_pending_*` buffer. `append_curve(stream_messages)` accumulates new points into the pending buffer; `flush()` sends them to the browser via `_extend_traces`.

`_extend_traces` bypasses NiceGUI's `fig.update()` / `Plotly.react()` by calling `Plotly.extendTraces` directly on the mounted Vue element via `client.run_javascript()`. This streams only the new delta to the client and avoids disrupting an in-progress pan or zoom gesture.

### `jupiterli/backend/config.py` — TTL Config Loader
`load_config(g, pl)` walks an already-parsed `rdflib.Graph` and builds the dashboard from it: each `jli:Plot` subject becomes a `Plot` (titled via `:title`), and each `jli:Scatter` / `jli:TimeseriesScatter` / `jli:Histogram` subject becomes a curve on its referenced `:on_plot`, subscribed to its `:key`. The `jli:` and `:` (scratch) namespaces are hardcoded to `http://example.com/jupiterli#` and `http://example.com/scratch#`.

### `jupiterli/backend/cli.py` — UI Wiring (entry point: `jupiterli-backend`)
`NiceGUIApplication.launch` is registered as the NiceGUI page handler for `/`. Each browser connection gets its own `ZmqLoop` and `PlotterLoop`, then calls `load_config(self.g, pl)` to instantiate plots/curves from the TTL config. The TTL path is taken from `sys.argv[1]` at module load (constant `TTL_PATH`). On disconnect the ZMQ polling task is cancelled.

`_watch_files` is an auto-restart watcher registered via `app.on_startup`. It polls `st_mtime` on `TTL_PATH` plus every `*.py` under `PKG_DIR` (the `jupiterli/backend/` package dir) every 1s; on any change it `os.execv`s the current interpreter with the original `sys.argv`, replacing the process in place. NiceGUI's own `reload=True` is not used because it does not work with console-script entry points (it re-imports the module under its dotted name, never hitting the `__main__`/`__mp_main__` guard).

`PlotterLoop.loop()` waits on `batch_is_done`, resets the event, and calls `plot.flush()` on every `Plot`. The one `fig.update()` call at the top of `loop()` (before the while loop) is an initial render trigger only.

### `examples/producer.py` — Synthetic Data Source
Publishes random integer values plus a `timestamp` field on ZMQ topics `data1` and `data2` every ~0.25s using `add_ts_point`. Run directly with `python examples/producer.py`. The PUB socket is bound on the first `add_ts_point` call (lazy init in `jupiterli/__init__.py`).

### `examples/producer.ttl` — Dashboard Config
Turtle/RDF file declaring the plots and curves for the dashboard to render. Curves carry a `jli:key` predicate naming the ZMQ topic to subscribe to. Instance subjects (`:fig1`, `:fig2`, `:fig3` and their curves) are validated against the SHACL shapes in `jupiterli/backend/ttl/jli-shacl.ttl`, which `cli.py` parses alongside the user TTL. The SHACL shapes are documentation/validation only — `load_config` reads the instance triples, not the shapes. Validate with `pyshacl -i rdfs examples/producer.ttl -f human`.

## Key Design Decisions

- **PUB/SUB transport**: Producer binds a `zmq.PUB` socket on `tcp://*:5555`; each browser session connects a `zmq.SUB` socket back. ZMQ does not buffer for late subscribers, so messages published before a browser tab opens are dropped — fine for a continuous data demo.
- **Multi-frame messages**: Each message is `[topic_bytes, json_bytes]`. The topic frame drives ZMQ's native subscription filter (`setsockopt(SUBSCRIBE, key)`); the JSON frame carries the payload dict.
- **String-valued payloads downstream**: `ZmqLoop` converts every payload field to `str(...)` before handing it to subscribers, matching what `redis.from_url(..., decode_responses=True)` used to return. This keeps the existing `float(it['value'])` / `float(it['timestamp'])` calls in `plots.py` working unchanged.
- **Batch signal**: `ZmqLoop` fires one `asyncio.Event` per 0.5s cycle (only if messages actually arrived), so the UI updates once per polling interval rather than once per message.
- **Per-client isolation**: `NiceGUIApplication.launch` creates a fresh `ZmqLoop` + `PlotterLoop` per browser connection; disconnect cancels the ZMQ task and closes the socket.
- **extendTraces over react**: Live updates use `Plotly.extendTraces` via raw JavaScript rather than `Plotly.react`, so pan/zoom state is preserved during streaming updates.
- **ZMQ endpoints**: Hardcoded as `tcp://*:5555` in `jupiterli/__init__.py` (producer bind) and `tcp://localhost:5555` in `jupiterli/backend/zmq_utils.py` (backend connect) — change both if running across hosts.
- **Stream message schema**: Each message's JSON payload must contain at minimum a `"value"` field (numeric). `TimeseriesScatter` additionally requires a `"timestamp"` field (Unix epoch float).
- **TTL-driven dashboard**: Plots and curves are declared in a Turtle file (`examples/producer.ttl`) rather than hardcoded in `cli.py`. Adding or reconfiguring a chart means editing the TTL, not the Python. The config path is `sys.argv[1]` to `jupiterli-backend`.
- **In-process restart-on-change**: `cli.py` polls mtimes of the TTL file and all package `*.py` files and `os.execv`s on any change, instead of using NiceGUI's `reload=True` (which is incompatible with the console-script entry point).
