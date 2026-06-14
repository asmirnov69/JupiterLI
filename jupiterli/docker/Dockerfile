FROM node:24 AS frontend-build

RUN apt-get update && apt-get install -y git \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /workspace
#RUN git clone --branch jupiterli-browser-ready --depth 1 --single-branch https://github.com/asmirnov69/JupiterLI-browser.git
RUN git clone --branch main --depth 1 --single-branch https://github.com/asmirnov69/JupiterLI-browser.git
WORKDIR /workspace/JupiterLI-browser/frontend
RUN npm ci
RUN npm run build

from ubuntu:22.04

ARG CURR_UID
ARG CURR_GID

USER root

RUN apt-get update && \
    apt-get install -y gettext-base redis python3.10 python3.10-venv git curl && \
    rm -rf /var/lib/apt/lists/*

COPY --chmod=755 docker-start.sh /

RUN mkdir /host-user-apps
COPY redis-sqlite3-intake.py /host-user-apps/

##RUN git clone --branch jupiterli-browser-ready --depth 1 --single-branch https://github.com/asmirnov69/JupiterLI-browser.git /host-user-apps/JupiterLI-browser
COPY --from=frontend-build /workspace/JupiterLI-browser/backend /host-user-apps/JupiterLI-browser/backend
COPY --from=frontend-build /workspace/JupiterLI-browser/frontend/dist /host-user-apps/JupiterLI-browser/frontend/dist
RUN cd /host-user-apps/JupiterLI-browser/backend && python3 -m venv venv && venv/bin/pip install -r ./requirements.txt && venv/bin/pip install httpx
COPY simple_website.py /host-user-apps/JupiterLI-browser/backend

RUN chown -R ${CURR_UID}:${CURR_GID} /host-user-apps

ENTRYPOINT ["/docker-start.sh"]
