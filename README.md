# JupiterLI

JupiterLI - named after small Jupiter moon [Jupiter LI](https://en.wikipedia.org/wiki/Jupiter_LI)

Real-time telemetry data visualization dashboard. Data to be shown can be produced by any python code, see examples/producer.py. Resulting timeseries will be observable via JupiterLI-browser webapp.

Python package JupiterLI provides API to allow reporting values to remote application to provide measurements. 

The way how API implemented is Redis stream which is populated by API call of client library. The data intake server (redis-clickhouse-intake.py) inserts data from Redis stream listening end into clickhouse database.
JUpiterLI-browser is web-based application. Python Flask backend has access to both Redis streams and clieckhouse database. Typescript frontend provides time-series view of collected telemetry data.

JupiterLI python package provides CLI to create and manage podman container where three components are configured and running: Redis server, clickhouse database server and JupiterLI-browser backend. JupiterLI-browser frontend webapp can be used via browser.

## Install JupiterLI

First make sure podman is installed on your system

```bash
apt install podman
```

pip install JupiterLI from github repo:

```bash
python3 -m venv <venv-dir-of-your-choice>
source <venv-dir-of-your-choice>/bin/activate
pip install git+https://github.com/asmirnov69/JupiterLI
```

## Run JupiterLI

```bash
source <venv-dir-of-your-choice>/bin/activate
jupiterli verify # should print version of podman
jupiterli init --data-dir <local dir for jupiterli podman container>
jupiterli start
jupiterli status
```

JupipterLI is now ready to accept telemetry information. It should be observable on JupiterLI-browser webapp which is running on the same host port 5173.
To access that open http://localhost:5173 in your browser.

## Run example

In one terminal, start the data producer (publishes random values to Redis every 2.5s):
```bash
source <venv-dir-of-your-choice>/bin/activate
pip install git+https://github.com/asmirnov69/libJupiterLI
python examples/producer.py
```

# podman reset

Usual command to reset podman:
```
podman system reset -f
```

In the case of errors this command sequence should help to fix errors.
```
systemctl --user stop podman.socket
systemctl --user stop podman.service

rm -rf ~/.local/share/containers
rm -rf ~/.config/containers
rm -rf ~/.cache/containers

podman system reset -f
```
