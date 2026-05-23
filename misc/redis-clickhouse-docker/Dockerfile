FROM docker.io/clickhouse/clickhouse-server:latest

USER root

RUN apt-get update && \
    apt-get install -y gettext-base redis python3 python3-pip python3.10-venv && \
    rm -rf /var/lib/apt/lists/*


COPY --chmod=700 docker-start.sh /
COPY redis-clickhouse-intake.py /

ENTRYPOINT ["/docker-start.sh"] # run redis then uses default clickhouse image entrypoint

