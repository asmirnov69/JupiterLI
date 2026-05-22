FROM docker.io/clickhouse/clickhouse-server:latest

USER root

RUN apt-get update && \
    apt-get install -y gettext-base redis && \
    rm -rf /var/lib/apt/lists/*


COPY --chmod=700 docker-start.sh /
ENTRYPOINT ["/docker-start.sh"] # run redis then uses default clickhouse image entrypoint

