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
./run.sh # will run container, use podman ps to check that
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
