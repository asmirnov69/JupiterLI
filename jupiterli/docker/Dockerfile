FROM alpine:3.22

ARG CURR_UID
ARG CURR_GID

USER root

RUN apk add --no-cache \
    bash \
    gettext \
    python3 \
    py3-pip \
    mosquitto

COPY --chmod=755 docker-start.sh /

RUN mkdir /host-user-apps
COPY mosquitto.conf /host-user-apps/
COPY mqtt-sqlite3-intake.py /host-user-apps/
COPY db-access-backend/ /host-user-apps/db-access-backend/

RUN chown -R ${CURR_UID}:${CURR_GID} /host-user-apps

ENTRYPOINT ["/docker-start.sh"]
