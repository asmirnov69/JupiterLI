#!/bin/bash
set -e

sudo rm -rf clickhouse-data
mkdir clickhouse-data
podman build -t my-redis-clickhouse .
