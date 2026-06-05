# JupiterLI

JupiterLI - named after small Jupiter moon [Jupiter LI](https://en.wikipedia.org/wiki/Jupiter_LI)

Real-time telemetry data visualization dashboard. Data to be shown can be produced by any python code, see examples/producer.py. Resulting timeseries will be observable via JupiterLI-browser webapp.

Python package JupiterLI provides API to allow reporting values to remote application to provide measurements. 

The way how API implemented is Redis stream which is populated by API call of client library. The data intake server (redis-clickhouse-intake.py) inserts data from Redis stream listening end into clickhouse database.
JUpiterLI-browser is web-based application. Python Flask backend has access to both Redis streams and clieckhouse database. Typescript frontend provides time-series view of collected telemetry data.

JupiterLI python package provides CLI to create and manage podman container where three components are configured and running: Redis server, clickhouse database server and JupiterLI-browser backend. JupiterLI-browser frontend webapp can be used via browser.

## Install JupiterLI

```bash
pip install git+https://github.com/asmirnov69/JupiterLI
```

## Run the example

```bash
jupiterli-podman init --data-dir <local dir for jupiterli podman container>
jupiterli-podman start
```

In one terminal, start the data producer (publishes random values to Redis every 2.5s):
```bash
python examples/producer.py
```

Then open http://localhost:5173 in your browser.

