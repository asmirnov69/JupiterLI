FROM docker.io/clickhouse/clickhouse-server:latest
ARG CURR_UID
ARG CURR_GID

USER root

RUN apt-get update && \
    apt-get install -y gettext-base redis python3 python3-pip python3.10-venv git curl && \
    rm -rf /var/lib/apt/lists/*

ENV NVM_DIR=/usr/local/nvm
RUN mkdir -p $NVM_DIR
RUN curl -fsSL https://raw.githubusercontent.com/nvm-sh/nvm/v0.40.3/install.sh | bash

RUN . $NVM_DIR/nvm.sh && nvm install 24 && nvm alias default 24 && nvm use default
RUN ln -s $NVM_DIR/versions/node/$(ls $NVM_DIR/versions/node)/bin/node /usr/local/bin/node \
    && ln -s $NVM_DIR/versions/node/$(ls $NVM_DIR/versions/node)/bin/npm /usr/local/bin/npm \
    && ln -s $NVM_DIR/versions/node/$(ls $NVM_DIR/versions/node)/bin/npx /usr/local/bin/npx

RUN echo "CURR_UID is: $CURR_UID" && echo "CURR_GID is: $CURR_GID"
RUN mkdir /host-user-apps && chown ${CURR_UID}:${CURR_GID} /host-user-apps
COPY --chmod=755 docker-start.sh /

RUN git clone --branch jupiterli-browser-ready --depth 1 --single-branch https://github.com/asmirnov69/JupiterLI-browser.git /host-user-apps/JupiterLi-browser
COPY redis-clickhouse-intake.py /host-user-apps/
RUN cd /host-user-apps/JupiterLi-browser/backend && python3 -m venv venv && venv/bin/pip install -r ./requirements.txt
RUN cd /host-user-apps/JupiterLi-browser/frontend && npm install
RUN chown -R ${CURR_UID}:${CURR_GID} /host-user-apps

ENTRYPOINT ["/docker-start.sh"] # run redis then uses default clickhouse image entrypoint

