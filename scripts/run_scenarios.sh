#!/usr/bin/env bash
set -e

# Script to run multiple scenarios for ProcessSample optimization testing
# Usage: ./scripts/run_scenarios.sh [duration_minutes]

DURATION_MINUTES=${1:-30}
RESULTS_DIR="./results"
TIMESTAMP=$(date +%Y%m%d_%H%M%S)

echo "🚀 Starting ProcessSample optimization scenario tests"
echo "🕒 Each scenario will run for ${DURATION_MINUTES} minutes"

# Create results directory
mkdir -p "${RESULTS_DIR}"
mkdir -p "${RESULTS_DIR}/${TIMESTAMP}"

# Function to run a scenario
run_scenario() {
  local name=$1
  local compose_files=$2
  local description=$3
  local start_time=$(date +%s)
  
  echo "===================================="
  echo "📊 Starting scenario: ${name}"
  echo "🔎 ${description}"
  echo "===================================="
  
  # Stop any running containers
  docker compose down || true
  
  # Start the scenario with the specified compose files
  COMPOSE_FILE="${compose_files}" docker compose up -d
  
  # Check if containers are healthy
  sleep 30
  if ! docker compose ps | grep -q "healthy"; then
    echo "❌ Containers failed to start healthy for scenario ${name}"
    docker compose logs
    docker compose down
    return 1
  fi
  
  echo "✅ Scenario ${name} started successfully"
  echo "⏳ Running for ${DURATION_MINUTES} minutes to collect data..."
  
  # Sleep for the specified duration
  sleep $((DURATION_MINUTES * 60))
  
  # Validate ingest stats and save to results
  echo "📈 Collecting metrics..."
  ./scripts/validate_ingest.sh > "${RESULTS_DIR}/${TIMESTAMP}/${name}_results.txt"
  
  # Get logs and save to results
  docker compose logs > "${RESULTS_DIR}/${TIMESTAMP}/${name}_logs.txt"
  
  # Stop the scenario
  docker compose down
  
  local end_time=$(date +%s)
  local elapsed_time=$((end_time - start_time))
  local elapsed_minutes=$((elapsed_time / 60))
  local elapsed_seconds=$((elapsed_time % 60))
  
  echo "✅ Completed scenario: ${name} in ${elapsed_minutes}m ${elapsed_seconds}s"
  
  # Add small delay between scenarios
  sleep 10
}

# Run the baseline scenario (20s, no filtering)
baseline_setup() {
  echo "Setting up baseline configuration..."
  # Create a temporary newrelic-infra.yml with 20s sampling and no filtering
  cat > config/newrelic-infra.yml.baseline << EOF
license_key: ${NEW_RELIC_LICENSE_KEY}
enable_process_metrics: true
metrics_process_sample_rate: 20
collect_process_commandline: false
EOF
  
  # Backup the original config
  mv config/newrelic-infra.yml config/newrelic-infra.yml.original
  # Use the baseline config
  mv config/newrelic-infra.yml.baseline config/newrelic-infra.yml
}

baseline_cleanup() {
  echo "Restoring original configuration..."
  # Restore the original config
  mv config/newrelic-infra.yml.original config/newrelic-infra.yml
}

# Run each scenario
echo "📝 Scenario results will be saved to ${RESULTS_DIR}/${TIMESTAMP}/"

# Standard Scenario (60s with filtering)
run_scenario "standard" "docker-compose.yml:docker-compose.override.yml:overrides/seccomp-disabled.yml" "Default configuration with 60s sampling and process filtering"

# Minimal Mounts Scenario
run_scenario "minimal_mounts" "docker-compose.yml:docker-compose.override.yml:overrides/min-mounts.yml:overrides/seccomp-disabled.yml" "Minimal filesystem mounts with 60s sampling"

# Container Metrics Scenario
run_scenario "container_metrics" "docker-compose.yml:docker-compose.override.yml:overrides/docker-stats.yml:overrides/seccomp-disabled.yml" "Container metrics via docker_stats with 60s process sampling"

# Baseline Scenario (20s, no filtering)
baseline_setup
run_scenario "baseline" "docker-compose.yml:docker-compose.override.yml:overrides/seccomp-disabled.yml" "Baseline configuration with 20s sampling and no filtering"
baseline_cleanup

# Generate summary report
echo "📊 Generating summary report..."
echo "# ProcessSample Optimization Scenarios Summary" > "${RESULTS_DIR}/${TIMESTAMP}/summary.md"
echo "Run timestamp: $(date)" >> "${RESULTS_DIR}/${TIMESTAMP}/summary.md"
echo "" >> "${RESULTS_DIR}/${TIMESTAMP}/summary.md"
echo "| Scenario | Description | ProcessSample Ingest (GB) |" >> "${RESULTS_DIR}/${TIMESTAMP}/summary.md"
echo "|----------|-------------|---------------------------|" >> "${RESULTS_DIR}/${TIMESTAMP}/summary.md"

# Extract the ingest GB for each scenario
for scenario in standard minimal_mounts container_metrics baseline; do
  ingest=$(grep "ProcessSample ingest" "${RESULTS_DIR}/${TIMESTAMP}/${scenario}_results.txt" | awk '{print $NF}')
  description=""
  case $scenario in
    standard) description="60s sampling with filtering" ;;
    minimal_mounts) description="Minimal filesystem mounts" ;;
    container_metrics) description="Container metrics via docker_stats" ;;
    baseline) description="20s sampling, no filtering" ;;
  esac
  echo "| ${scenario} | ${description} | ${ingest} |" >> "${RESULTS_DIR}/${TIMESTAMP}/summary.md"
done

echo "" >> "${RESULTS_DIR}/${TIMESTAMP}/summary.md"
echo "## Reduction Analysis" >> "${RESULTS_DIR}/${TIMESTAMP}/summary.md"
echo "" >> "${RESULTS_DIR}/${TIMESTAMP}/summary.md"

# Calculate reduction percentages
baseline_ingest=$(grep "ProcessSample ingest" "${RESULTS_DIR}/${TIMESTAMP}/baseline_results.txt" | awk '{print $NF}')
if [[ -n "$baseline_ingest" && "$baseline_ingest" != "N/A" ]]; then
  for scenario in standard minimal_mounts container_metrics; do
    scenario_ingest=$(grep "ProcessSample ingest" "${RESULTS_DIR}/${TIMESTAMP}/${scenario}_results.txt" | awk '{print $NF}')
    if [[ -n "$scenario_ingest" && "$scenario_ingest" != "N/A" ]]; then
      reduction=$(echo "scale=2; (1 - ${scenario_ingest}/${baseline_ingest}) * 100" | bc)
      echo "- ${scenario}: ${reduction}% reduction compared to baseline" >> "${RESULTS_DIR}/${TIMESTAMP}/summary.md"
    fi
  done
fi

echo "🎉 All scenarios completed! Results saved to ${RESULTS_DIR}/${TIMESTAMP}/"
echo "📋 Summary report: ${RESULTS_DIR}/${TIMESTAMP}/summary.md"
