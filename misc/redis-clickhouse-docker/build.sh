#!/bin/bash
set -e

rm -rf clickhouse-data
mkdir clickhouse-data
rm -rf docker-logs
mkdir docker-logs
podman build --build-arg CURR_UID=$(id -u) --build-arg CURR_GID=$(id -g) -t my-redis-clickhouse .
