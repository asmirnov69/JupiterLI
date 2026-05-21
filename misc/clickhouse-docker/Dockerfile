FROM docker.io/clickhouse/clickhouse-server:latest

USER root

RUN apt-get update && \
    apt-get install -y gettext-base && \
    rm -rf /var/lib/apt/lists/*

ENTRYPOINT ["/entrypoint.sh"] # default clickhouse image entrypoint

