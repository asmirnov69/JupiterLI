#!/bin/bash


echo "starting redis as daemon"
redis-server --bind 0.0.0.0 --protected-mode no --daemonize yes

echo "running clickhouse entrypoint.sh"
./entrypoint.sh &

echo "creating venv"
python3 -m venv /venv
echo "installing intake script deps"
/venv/bin/pip install redis clickhouse-driver
echo "running intake script"
exec /venv/bin/python /redis-clickhouse-intake.py >& /redis-clickhouse-intake.py.log

