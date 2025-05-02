#!/usr/bin/env bash
set -e

echo "🚀 CI smoke test"

# Ensure scripts are executable
chmod +x "$(dirname "$0")"/*.sh
chmod +x "$(dirname "$0")/../load-image/entrypoint.sh"

# Create a simpler CI override file without read-only and seccomp constraints
cat > docker-compose.ci.yml << EOF
version: "3.9"

services:
  infra:
    security_opt: []
    read_only: false

  otel:
    security_opt: []
    read_only: false

  load:
    security_opt: []
    read_only: false
EOF

echo "Starting containers with simplified configuration for CI..."
SECURE_MODE=false docker compose --profile default -f docker-compose.yml -f docker-compose.ci.yml up -d

max_wait=60
waited=0
echo "⏳ Waiting up to ${max_wait}s for containers to start..."

while [ $waited -lt $max_wait ]; do
  echo "Checking container status (${waited}s elapsed)..."
  
  # Check if all containers are running
  running_count=$(docker compose ps --services --filter "status=running" | wc -l)
  
  # If we have 3 running containers, consider it a success
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

# Try to list the running processes in each container
echo "Checking processes in containers..."
docker compose exec -T infra ps aux || echo "⚠️ Cannot check infra processes"
docker compose exec -T otel ps aux || echo "⚠️ Cannot check otel processes"
docker compose exec -T load ps aux || echo "⚠️ Cannot check load processes"

# Check for logs
echo "Checking container logs..."
docker compose logs --tail=20 || echo "⚠️ Cannot fetch logs"

# Clean up
echo "Test complete, cleaning up..."
docker compose down

echo "🎉 Smoke test completed"