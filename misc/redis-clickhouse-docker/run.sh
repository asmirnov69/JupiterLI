#!/bin/bash
set -e

CH_DATA_DIR=`pwd`/clickhouse-data
if [ -d ${CH_DATA_DIR} ]; then
    echo "found clickhouse datadir: ${CH_DATA_DIR}"
else
    echo "clickhouse datadir ${CH_DATA_DIR} does not exist, giving up..."
    exit 2
fi

podman run -d --name redis-clickhouse \
    -p 8123:8123 -p 9000:9000 -p 6379:6379 \
    -v "${CH_DATA_DIR}:/var/lib/clickhouse" \
    my-redis-clickhouse
