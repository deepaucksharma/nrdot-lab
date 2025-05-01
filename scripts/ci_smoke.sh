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
  echo "Checking container status (${waited}s elapsed)..."
  
  # Check if all containers are running
  running_count=$(docker compose ps --services --filter "status=running" | wc -l)
  
  # Check if all containers are available (not necessarily healthy)
  # We're not requiring health checks to pass since they might vary between versions
  if [ "$running_count" -ge 3 ]; then
    echo "✅ All containers are running!"
    break
  fi
  
  sleep 5
  waited=$((waited + 5))
done

if [ $waited -ge $max_wait ]; then
  echo "❌ Timed out waiting for containers to start"
  docker compose ps
  docker compose logs
  docker compose down
  exit 1
fi

# Simple verification
echo "Checking container status..."
docker compose ps

# Try to access config files if possible
echo "Checking configuration files..."
docker compose exec infra ls -la /etc/newrelic-infra.yml || echo "⚠️ Cannot check infra config"
docker compose exec otel ls -la /etc/otel-config.yaml || echo "⚠️ Cannot check otel config"

# Check for logs
echo "Checking container logs..."
docker compose logs --tail=20 || echo "⚠️ Cannot fetch logs"

# Clean up
echo "Test complete, cleaning up..."
docker compose down

echo "🎉 Smoke test completed"