```
clickhouse-docker/
├── Dockerfile
└── build.sh
```

build image:
```
./build.sh
```

run container:
```
mkdir ./clickhouse-data # this is location in host system where guest clickhouse will keep its files
export CH_DATA_DIR=`pwd`/clickhouse-data

podman run -d --name clickhouse \
    -p 8123:8123 -p 9000:9000 \
    -v "${CH_DATA_DIR}:/var/lib/clickhouse" \
    my-clickhouse
```

access:
```
podman exec -it clickhouse clickhouse-client # using default user with no password
```

DEBUGGING:

bash run without launch of specified in Dockerfile entry point:
```
podman run --rm -it --entrypoint bash my-clickhouse
```
