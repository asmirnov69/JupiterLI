FROM docker.io/clickhouse/clickhouse-server:latest
LABEL label=jupiterli-image

USER root

RUN apt-get update && \
    apt-get install -y gettext-base redis python3 python3-pip python3.10-venv && \
    rm -rf /var/lib/apt/lists/*

ARG CURR_UID
ARG CURR_GID
RUN echo "CURR_UID is: $CURR_UID" && echo "CURR_GID is: $CURR_GID"
RUN mkdir /host-user-apps && chown ${CURR_UID}:${CURR_GID} /host-user-apps
COPY --chmod=755 docker-start.sh /
COPY redis-clickhouse-intake.py /host-user-apps/

ENTRYPOINT ["/docker-start.sh"] # run redis then uses default clickhouse image entrypoint

