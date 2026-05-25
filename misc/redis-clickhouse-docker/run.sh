#!/bin/bash
set -e

CH_DATA_DIR=`pwd`/clickhouse-data
if [ -d ${CH_DATA_DIR} ]; then
    echo "found clickhouse datadir: ${CH_DATA_DIR}"
else
    echo "clickhouse datadir ${CH_DATA_DIR} does not exist, giving up..."
    exit 2
fi

LOGS_DIR=`pwd`/docker-logs
if [ -d ${LOGS_DIR} ]; then
    echo "found logs dir: ${LOGS_DIR}"
else
    echo "logs dir ${LOGS_DIR} does not exist, giving up..."
    exit 2
fi

podman run --rm -d \
       --name redis-clickhouse \
       --userns keep-id \
       --user $(id -u):$(id -g) \
       -e HOME=/host-user-apps \
       -p 8123:8123 \
       -p 9000:9000 \
       -p 6379:6379 \
       -p 5173:5173 \
       -v "$PWD/clickhouse-data:/var/lib/clickhouse:Z" \
       -v "$PWD/docker-logs:/logs:Z" \
         my-redis-clickhouse
