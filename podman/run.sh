echo "arg file: $1"

cp $1 jupiterli.ttl

cat > /tmp/Dockerfile.temp <<EOF
FROM jupiterli
COPY jupiterli.ttl /app/jupiterli.ttl
CMD ["/app/docker-start.sh"]
EOF

podman image rm -f temp-image
podman build -f /tmp/Dockerfile.temp -t temp-image .
rm -f jupiterli.ttl /tmp/Dockerfile.temp

podman run -d --rm -p 8080:8080 -p 6379:6379 temp-image
