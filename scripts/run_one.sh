#!/usr/bin/env bash
set -eo pipefail

# Default values
DURATION=${DURATION:-30}  # Default run time in minutes
SCEN=${SCEN:-"test"}      # Scenario identifier
SAMPLE=${SAMPLE:-60}      # Sample rate in seconds
FILTER=${FILTER:-"yes"}   # Process filtering enabled by default
STRESS_CPU=${STRESS_CPU:-2}
STRESS_MEM=${STRESS_MEM:-128M}
LOAD_STRESSOR=${LOAD_STRESSOR:-""}
PROFILE=${PROFILE:-"default"}

# Create results directory with timestamp
TIMESTAMP=$(date +%Y%m%d_%H%M%S)
RESULTS_DIR="results/${TIMESTAMP}"
mkdir -p "${RESULTS_DIR}"

echo "Running scenario ${SCEN} with sample rate ${SAMPLE}s for ${DURATION} minutes"

# Generate dynamic newrelic-infra.yml from template
echo "Generating infrastructure config..."
cat > config/newrelic-infra.yml <<EOF
license_key: \${NEW_RELIC_LICENSE_KEY}
enable_process_metrics: true
metrics_process_sample_rate: ${SAMPLE}
collect_process_commandline: false

# Modern filtering syntax (works with agent v1.40+)
EOF

if [ "$FILTER" = "yes" ]; then
  cat >> config/newrelic-infra.yml <<EOF
exclude_matching_metrics:
  process.name: ["systemd", "cron", "containerd", "dockerd", "sshd", "bash", "sh"]
  process.executable: ["/usr/bin/containerd", "/usr/sbin/cron", "/usr/bin/docker", "/usr/sbin/sshd"]
EOF
fi

# Handle OTel configuration if needed
if [ -n "$OTEL_INTERVAL" ]; then
  echo "Configuring OTel with ${OTEL_INTERVAL}s interval..."
  sed "s/collection_interval: 10s/collection_interval: ${OTEL_INTERVAL}s/g" config/otel-config.yaml > config/otel-config-temp.yaml
  mv config/otel-config-temp.yaml config/otel-config.yaml
fi

# Set environment variables for the load generator
export STRESS_CPU STRESS_MEM LOAD_STRESSOR

# Start containers with specified profile
echo "Starting containers with profile: ${PROFILE}..."
docker compose --profile "${PROFILE}" up -d

# Wait for the specified duration
echo "Running for ${DURATION} minutes..."
sleep $((DURATION * 60))

# Capture docker stats for resource usage
echo "Capturing resource metrics..."
docker stats --no-stream > "${RESULTS_DIR}/${SCEN}_docker_stats.txt"

# Run validation to get ingest metrics
echo "Validating ingest metrics..."
OUTPUT_JSON=true TIME_WINDOW=${DURATION} BASELINE_RATE=20 CURRENT_RATE=${SAMPLE} ./scripts/validate_ingest.sh > "${RESULTS_DIR}/${SCEN}_ingest.json"

# Calculate visibility delay if stress-ng is used
if docker ps | grep -q stress-load; then
  echo "Calculating visibility delay..."
  VIS_DELAY=$(python3 ./scripts/vis_latency.py)
  
  # Append visibility delay to the JSON file
  TMP_FILE=$(mktemp)
  jq --arg delay "$VIS_DELAY" '. + {"visibility_delay_s": $delay}' "${RESULTS_DIR}/${SCEN}_ingest.json" > "$TMP_FILE"
  mv "$TMP_FILE" "${RESULTS_DIR}/${SCEN}_ingest.json"
fi

# Combine all metrics into a final results JSON
echo "Generating final results..."
cat "${RESULTS_DIR}/${SCEN}_ingest.json" | \
  jq --arg scen "$SCEN" --arg profile "$PROFILE" --arg filter "$FILTER" \
     '. + {"scenario_id": $scen, "profile": $profile, "filtering": $filter}' \
  > "${RESULTS_DIR}/${SCEN}.json"

echo "Scenario ${SCEN} completed. Results saved to ${RESULTS_DIR}/${SCEN}.json"
