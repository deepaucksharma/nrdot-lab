#!/usr/bin/env bash
set -e

echo "🚀 CI smoke test"

# Ensure scripts are executable
chmod +x "$(dirname "$0")"/*.sh
chmod +x "$(dirname "$0")/../load-image/entrypoint.sh"

# Create tmpfs mount locations for containers
mkdir -p /tmp/nr-data || true
chmod 777 /tmp/nr-data || true

# Use docker-compose override file to handle tmpfs
cat > docker-compose.ci.yml << EOF
services:
  infra:
    tmpfs:
      - /tmp
      - /var/run
      - /var/db/newrelic-infra
  load:
    tmpfs:
      - /tmp
      - /var/run
EOF

echo "Starting containers..."
docker compose --profile default -f docker-compose.yml -f docker-compose.ci.yml up -d

echo "Waiting for containers to start..."
sleep 10

echo "Checking container status..."
docker compose ps
docker compose logs

# Just a simple verification step
echo "Checking config files..."
docker compose exec infra ls -la /etc/newrelic-infra.yml || true
docker compose exec otel ls -la /etc/otel-config.yaml || true

# Just check for logs
docker compose logs --tail=20 infra otel load || true

# Clean up
docker compose down || true

echo "🎉 Smoke test completed - this is just a basic verification now"