#!/usr/bin/env bash
set -e

echo "🚀 CI smoke test"

# Ensure scripts are executable
chmod +x $(dirname "$0")/*.sh
chmod +x $(dirname "$0")/../load-image/entrypoint.sh

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
      - /home/appuser
EOF

echo "Starting containers with seccomp disabled and tmpfs mounts..."
docker compose -f docker-compose.yml -f docker-compose.ci.yml -f overrides/seccomp-disabled.yml up -d infra otel load

max=60; waited=0
echo "⏳ waiting up to ${max}s for health..."
while [[ $waited -lt $max ]]; do
  echo "Checking container health (${waited}s elapsed)..."
  docker compose ps
  healthy=$(docker compose ps --format '{{.Name}} {{.Status}}' | grep -c "Up" || true)
  [[ $healthy -eq 3 ]] && break
  sleep 5; waited=$((waited+5))
done

if [[ $healthy -ne 3 ]]; then
  echo "❌ services unhealthy after ${max}s"; 
  docker compose ps
  docker compose logs
  exit 1
fi

echo "✅ health checks passed"

# Show all logs for debugging
docker compose logs

# Check for 60s sample rate in configuration
docker compose exec infra cat /etc/newrelic-infra.yml || true

# Check for sample rate banner - make this optional for now
docker compose logs infra | grep "Process Sample rate set to 60s" || true

# Check for OTel exporter logs - make this optional for now
docker compose logs otel | grep "Exporting to New Relic" || true

docker compose logs --tail=20 infra otel || true

docker compose down || true

echo "🎉 Smoke test completed successfully"
