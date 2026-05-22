#!/bin/bash

echo "starting redis as daemon"
redis-server --bind 0.0.0.0 --protected-mode no --daemonize yes

echo "running clickhouse entrypoint.sh"
exec ./entrypoint.sh
