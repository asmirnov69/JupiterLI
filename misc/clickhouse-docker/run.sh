#!/bin/bash
set -e

CH_DATA_DIR=`pwd`/clickhouse-data
if [ -d ${CH_DATA_DIR} ]; then
    echo "found clickhouse datadir: ${CH_DATA_DIR}"
else
    echo "clickhouse datadir ${CH_DATA_DIR} does not exist, giving up..."
    exit 2
fi

podman run -d --name clickhouse \
    -p 8123:8123 -p 9000:9000 \
    -v "${CH_DATA_DIR}:/var/lib/clickhouse" \
    my-clickhouse
