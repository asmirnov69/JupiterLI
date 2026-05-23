#!/bin/bash
set -e

sudo rm -rf clickhouse-data
mkdir clickhouse-data
rm -rf docker-logs
mkdir docker-logs
podman build -t my-redis-clickhouse .
