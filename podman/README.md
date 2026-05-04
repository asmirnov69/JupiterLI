```
###  podman system reset -f -- full reset, everything will be gone

podman build -t alpine-test .
podman run --rm -p 8080:8080 -p 6379:6379 -v ../examples/producer.ttl:/app/jupiterli.ttl:Z alpine-test ./start.sh
```

```
podman run --name peaceful_lumiere -p 8080:8080 -p 6379:6379 alpine-test

podman create --name peaceful_lumiere -p 8080:8080 -p 6379:6379 alpine-test
podman start peaceful_lumiere
#podman exec -it peaceful_lumiere bash
podman exec -it peaceful_lumiere /app/venv/bin/jupiterli /app/JupiterLI/examples/producer.ttl

# /app/venv/bin/jupiterli /app/JupiterLI/examples/producer.ttl

podman run -rm -p 8080:8080 -p 6379:6379 alpine-test /app/venv/bin/jupiterli /app/JupiterLI/examples/producer.ttl
```
