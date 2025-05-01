#!/usr/bin/env bash
set -e

echo "🚀 CI smoke test"

# Create tmpfs mount locations for containers
mkdir -p /tmp/nr-data
chmod 777 /tmp/nr-data

docker compose -f docker-compose.yml -f overrides/seccomp-disabled.yml up -d infra otel load

max=60; waited=0
echo "⏳ waiting up to ${max}s for health..."
while [[ $waited -lt $max ]]; do
  healthy=$(docker compose -f docker-compose.yml -f overrides/seccomp-disabled.yml ps --format '{{.Name}} {{.State.Health.Status}}' \
            | grep -E 'nr-infra|otel-collector|stress-load' | grep -c healthy || true)
  [[ $healthy -eq 3 ]] && break
  sleep 5; waited=$((waited+5))
done

if [[ $healthy -ne 3 ]]; then
  echo "❌ services unhealthy after ${max}s"; docker compose ps; exit 1; fi

echo "✅ health checks passed"

# Check for sample rate banner
if ! docker compose -f docker-compose.yml -f overrides/seccomp-disabled.yml logs infra | grep -q "Process Sample rate set to 60s"; then
  echo "❌ Infra agent did not log 60s sample-rate banner"; exit 1; fi

# Check for OTel exporter logs
if ! docker compose -f docker-compose.yml -f overrides/seccomp-disabled.yml logs otel | grep -q "Exporting to New Relic"; then
  echo "❌ OTel exporter not sending telemetry"; exit 1; fi

docker compose -f docker-compose.yml -f overrides/seccomp-disabled.yml logs --tail=20 infra otel

docker compose -f docker-compose.yml -f overrides/seccomp-disabled.yml down

echo "🎉 Smoke test completed successfully"