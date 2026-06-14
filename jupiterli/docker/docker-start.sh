#!/bin/bash

set -x

echo "docker-start.sh as user `id -a`"

# redis
echo "starting redis as daemon"
redis-server --bind 0.0.0.0 --protected-mode no --daemonize yes
echo "Waiting for redis..."
until redis-cli ping >/dev/null 2>&1; do
    sleep 1
done
echo "redis is ready"

# JupiterLI-browser
echo "running JupiterLI-browser backend"
cd /host-user-apps/JupiterLI-browser/backend
venv/bin/uvicorn app.main:app --reload >& /logs/backend.logs &

echo "running JupiterLI-browser frontend"
venv/bin/uvicorn simple_website:app --host 0.0.0.0 --port 5173 >& /logs/simple_website.log &

sleep 3

# redis-sqlite3-intake
echo "creating venv"
python3 -m venv /host-user-apps/venv
echo "installing intake script deps"
/host-user-apps/venv/bin/pip install redis

echo "running intake script"
/host-user-apps/venv/bin/python -u /host-user-apps/redis-sqlite3-intake.py /sqlite3-data/data.db >& /logs/redis-sqlite3-intake.py.log &

echo "docker-start.sh done"
exec sleep 2147483647

