from ubuntu:22.04

ARG CURR_UID
ARG CURR_GID

USER root

RUN apt-get update && apt-get install -y software-properties-common \
    && apt-get install -y gettext-base redis python3.10 python3.10-venv git curl \
    && rm -rf /var/lib/apt/lists/*

RUN apt-add-repository ppa:mosquitto-dev/mosquitto-ppa \
    && apt-get update \
    && apt-get install -y mosquitto \
    && rm -rf /var/lib/apt/lists/*

COPY --chmod=755 docker-start.sh /

RUN mkdir /host-user-apps
COPY mosquitto.conf /host-user-apps/
COPY mqtt-sqlite3-intake.py /host-user-apps/
COPY db-access-backend/ /host-user-apps/db-access-backend/

RUN chown -R ${CURR_UID}:${CURR_GID} /host-user-apps

ENTRYPOINT ["/docker-start.sh"]
