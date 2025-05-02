#!/usr/bin/env bash
# Simple healthcheck for infrastructure agent and OTel collector

# Check infrastructure agent
echo "Checking New Relic Infrastructure Agent..."
INFRA_HEALTH=$(docker exec nr-infra curl -s http://localhost:18003/status 2>/dev/null)
if [ $? -eq 0 ] && [[ "$INFRA_HEALTH" == *"agent status"* ]]; then
  echo "✅ Infrastructure agent is healthy"
  INFRA_OK=true
else
  echo "❌ Infrastructure agent is not responding"
  INFRA_OK=false
fi

# Check OTel collector if it's running
if docker ps | grep -q "otel-collector"; then
  echo "Checking OpenTelemetry Collector..."
  OTEL_HEALTH=$(docker exec otel-collector wget -qO- http://localhost:13133/healthz 2>/dev/null)
  if [ $? -eq 0 ] && [[ "$OTEL_HEALTH" == *"healthcheck status"* ]]; then
    echo "✅ OpenTelemetry collector is healthy"
    OTEL_OK=true
  else
    echo "❌ OpenTelemetry collector is not responding"
    OTEL_OK=false
  fi
else
  echo "ℹ️ OpenTelemetry collector is not running"
  OTEL_OK=true  # Not running is OK if it's not part of the scenario
fi

# Return combined status
if [ "$INFRA_OK" = true ] && [ "$OTEL_OK" = true ]; then
  echo "🟢 All components healthy"
  exit 0
else
  echo "🔴 One or more components unhealthy"
  exit 1
fi