#!/bin/bash
#
# OpenTelemetry configuration generator for ProcessSample Optimization Lab
# Creates OTel configurations from template with different intervals
#

set -e

echo "Generating OpenTelemetry configuration files from template..."

# Directory setup
CONFIG_DIR="./config"
TEMPLATE_FILE="$CONFIG_DIR/otel-template.yaml"

# Check if template exists
if [ ! -f "$TEMPLATE_FILE" ]; then
  echo "Error: Template file $TEMPLATE_FILE not found!"
  exit 1
fi

# Function to generate OTel config with specific interval
generate_otel_config() {
  local interval=$1
  local output_file="$CONFIG_DIR/otel-${interval}s.yaml"
  local docker_stats=${2:-false}
  
  echo "Generating $output_file with interval ${interval}s..."
  
  # Create a temporary environment for variable substitution
  export INTERVAL="${interval}s"
  
  if [ "$docker_stats" = "true" ]; then
    export ENABLE_DOCKER_STATS="true"
  else
    unset ENABLE_DOCKER_STATS
  fi
  
  # Process template with environment variable substitution
  # This uses envsubst which is part of gettext package
  if command -v envsubst &> /dev/null; then
    envsubst < "$TEMPLATE_FILE" > "$output_file"
  else
    # Fallback to manual replacement if envsubst is not available
    cat "$TEMPLATE_FILE" | sed "s/\${INTERVAL:-10s}/\${INTERVAL:-${interval}s}/g" > "$output_file"
    
    # Handle Docker stats
    if [ "$docker_stats" = "true" ]; then
      sed -i "s/\${ENABLE_DOCKER_STATS:+docker}/docker/g" "$output_file"
      sed -i "s/\${ENABLE_DOCKER_STATS:+collection_interval: \${INTERVAL:-10s}}/collection_interval: \${INTERVAL:-${interval}s}/g" "$output_file"
      sed -i "s/\${ENABLE_DOCKER_STATS:+endpoint: unix:\/\/\/var\/run\/docker.sock}/endpoint: unix:\/\/\/var\/run\/docker.sock/g" "$output_file"
      sed -i "s/\${ENABLE_DOCKER_STATS:+timeout: 20s}/timeout: 20s/g" "$output_file"
      sed -i "s/\${ENABLE_DOCKER_STATS:+api_version: 1.24}/api_version: 1.24/g" "$output_file"
      sed -i "s/\${ENABLE_DOCKER_STATS:+, docker}/, docker/g" "$output_file"
    else
      sed -i "s/\${ENABLE_DOCKER_STATS:+docker}//g" "$output_file"
      sed -i "s/\${ENABLE_DOCKER_STATS:+collection_interval: \${INTERVAL:-10s}}//g" "$output_file"
      sed -i "s/\${ENABLE_DOCKER_STATS:+endpoint: unix:\/\/\/var\/run\/docker.sock}//g" "$output_file"
      sed -i "s/\${ENABLE_DOCKER_STATS:+timeout: 20s}//g" "$output_file"
      sed -i "s/\${ENABLE_DOCKER_STATS:+api_version: 1.24}//g" "$output_file"
      sed -i "s/\${ENABLE_DOCKER_STATS:+, docker}//g" "$output_file"
    fi
  fi
  
  # Normalize any remaining environment variables
  sed -i "s/\${HOSTNAME}/otel-collector/g" "$output_file"
  
  echo "Generated $output_file"
}

# Generate main config file (default 10s interval)
cp "$TEMPLATE_FILE" "$CONFIG_DIR/otel-config.yaml"
echo "Generated default config as otel-config.yaml"

# Generate configurations with different intervals
generate_otel_config 5
generate_otel_config 10
generate_otel_config 20
generate_otel_config 30

# Generate docker stats config
generate_otel_config 10 true
mv "$CONFIG_DIR/otel-10s.yaml" "$CONFIG_DIR/otel-docker.yaml"

# Generate a lightweight config with fewer scrapers
LITE_CONFIG="$CONFIG_DIR/otel-scr-lite.yaml"
echo "Generating lightweight config $LITE_CONFIG..."
cat "$TEMPLATE_FILE" | grep -v -E "(disk|filesystem|paging|network|process)" > "$LITE_CONFIG"
echo "Generated $LITE_CONFIG"

echo "OpenTelemetry configuration generation complete."
