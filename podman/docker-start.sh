#!/bin/sh

set -x  # 👈 shows executed commands

echo "Starting Redis..."
#exec redis-server --bind 0.0.0.0 --protected-mode no
redis-server --bind 0.0.0.0 --protected-mode no --daemonize yes
echo "staring jupiterli"

# this requires mount of host file to /app/jupiterli.ttl
exec /app/venv/bin/jupiterli /app/jupiterli.ttl
