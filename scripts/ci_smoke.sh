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
  otel:
    tmpfs:
      - /tmp
      - /var/run
  load:
    tmpfs:
      - /tmp
      - /var/run
EOF

echo "Starting containers..."
SECURE_MODE=true docker compose --profile default -f docker-compose.yml -f docker-compose.ci.yml up -d

max_wait=60
waited=0
echo "⏳ Waiting up to ${max_wait}s for containers to be healthy..."

while [ $waited -lt $max_wait ]; do
  echo "Checking container health (${waited}s elapsed)..."
  
  # Check if all containers are running
  running_count=$(docker compose ps --services --filter "status=running" | wc -l)
  
  # Check if all running containers are healthy
  healthy_count=$(docker compose ps --services --filter "health=healthy" | wc -l)
  
  # We need at least 3 containers (infra, otel, load)
  if [ "$running_count" -ge 3 ] && [ "$healthy_count" -ge 3 ]; then
    echo "✅ All containers are running and healthy!"
    break
  fi
  
  # If containers are running but unhealthy after 30s, something is wrong
  if [ $waited -gt 30 ] && [ "$running_count" -ge 3 ] && [ "$healthy_count" -lt 3 ]; then
    echo "❌ Containers are running but not all are healthy after ${waited}s"
    docker compose ps
    docker compose logs
    docker compose down
    exit 1
  fi
  
  sleep 5
  waited=$((waited + 5))
done

if [ $waited -ge $max_wait ]; then
  echo "❌ Timed out waiting for containers to be healthy"
  docker compose ps
  docker compose logs
  docker compose down
  exit 1
fi

# Verify configuration
echo "Checking Infrastructure Agent configuration..."
docker compose exec infra cat /etc/newrelic-infra.yml || (echo "❌ Failed to read Infrastructure configuration"; exit 1)

echo "Checking OpenTelemetry configuration..."
docker compose exec otel cat /etc/otel-config.yaml || (echo "❌ Failed to read OpenTelemetry configuration"; exit 1)

# Verify logs for expected patterns
echo "Verifying Infrastructure Agent logs..."
if ! docker compose logs infra | grep -q "Starting New Relic Infrastructure"; then
  echo "❌ Infrastructure Agent is not starting properly"
  docker compose logs infra
  docker compose down
  exit 1
fi

echo "Verifying OpenTelemetry Collector logs..."
if ! docker compose logs otel | grep -q "Starting OpenTelemetry Collector"; then
  echo "❌ OpenTelemetry Collector is not starting properly"
  docker compose logs otel
  docker compose down
  exit 1
fi

echo "Verifying load generator logs..."
if ! docker compose logs load | grep -q "stress-ng"; then
  echo "❌ Load generator is not running properly"
  docker compose logs load
  docker compose down
  exit 1
fi

# Clean up
echo "All checks passed! Cleaning up..."
docker compose down

echo "🎉 Smoke test completed successfully"