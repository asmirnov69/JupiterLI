#!/bin/bash

set -x

echo "docker-start.sh as user `id -a`"

echo "starting redis as daemon"
redis-server --bind 0.0.0.0 --protected-mode no --daemonize yes
echo "Waiting for redis..."
until redis-cli ping >/dev/null 2>&1; do
    sleep 1
done
echo "redis is ready"

echo "running clickhouse entrypoint.sh"
./entrypoint.sh &

echo "Waiting for clickhouse..."
until clickhouse-client --query "SELECT 1" >/dev/null 2>&1; do
    sleep 1
done
echo "clickhouse is ready"

echo "running JupiterLI-browser backend"
cd /host-user-apps/JupiterLi-browser/backend
venv/bin/uvicorn app.main:app --reload >& /logs/backend.logs &

cd ../frontend
NO_COLOR=1 FORCE_COLOR=0 npm run dev  < /dev/null >& /logs/frontend.log &

sleep 3

echo "creating venv"
python3 -m venv /host-user-apps/venv
echo "installing intake script deps"
/host-user-apps/venv/bin/pip install redis clickhouse-driver

echo "running intake script"
exec /host-user-apps/venv/bin/python -u /host-user-apps/redis-clickhouse-intake.py >& /logs/redis-clickhouse-intake.py.log

