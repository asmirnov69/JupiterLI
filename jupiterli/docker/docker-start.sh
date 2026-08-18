#!/bin/bash

set -x

echo "docker-start.sh as user `id -a`"

# mosquitto start
echo "starting mosquitto"
mosquitto -c /host-user-apps/mosquitto.conf >& /logs/mosquitto.log &

# JupiterLI-browser
echo "running JupiterLI-browser backend"
cd /host-user-apps/JupiterLI-browser/backend
venv/bin/uvicorn app.main:app --reload >& /logs/backend.logs &

echo "running JupiterLI-browser frontend"
venv/bin/uvicorn simple_website:app --host 0.0.0.0 --port 5173 >& /logs/simple_website.log &

sleep 3

# mqtt-sqlite3-intake
echo "creating venv"
python3 -m venv /host-user-apps/venv
echo "installing intake script deps"
/host-user-apps/venv/bin/pip install paho-mqtt

echo "running intake script"
#/host-user-apps/venv/bin/python -u /host-user-apps/mqtt-sqlite3-intake.py /sqlite3-data/data.db >& /logs/mqtt-sqlite3-intake.py.log &

echo "docker-start.sh done"
exec sleep 2147483647
