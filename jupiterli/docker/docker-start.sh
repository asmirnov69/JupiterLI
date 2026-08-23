#!/bin/bash

set -x

echo "docker-start.sh as user `id -a`"

echo "starting mosquitto"
mosquitto -c /host-user-apps/mosquitto.conf >& /logs/mosquitto.log &

sleep 3

# mqtt-sqlite3-intake
echo "creating venv"
python3 -m venv /host-user-apps/venv
echo "installing intake script deps"
/host-user-apps/venv/bin/pip install paho-mqtt

echo "installing db access script deps"
/host-user-apps/venv/bin/pip install -r /host-user-apps/db-access-backend/requirements.txt

echo "starting db access server"
/host-user-apps/venv/bin/uvicorn --host=0.0.0.0 --app-dir=/host-user-apps/db-access-backend app.main:app --reload --reload-dir=/host-user-apps/db-access-backend >& /logs/db-access-server.log &

echo "running intake script"
/host-user-apps/venv/bin/python -u /host-user-apps/mqtt-sqlite3-intake.py /sqlite3-data/data.db >& /logs/mqtt-sqlite3-intake.py.log &

echo "docker-start.sh done"
exec sleep 2147483647
