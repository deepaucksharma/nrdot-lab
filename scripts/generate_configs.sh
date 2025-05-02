#!/bin/bash
#
# Configuration generator for ProcessSample Optimization Lab
# Creates NewRelic Infrastructure configurations from templates
#

set -e

echo "Generating New Relic Infrastructure configuration files from templates..."

# Directory setup
CONFIG_DIR="./config"
TEMPLATE_FILE="$CONFIG_DIR/newrelic-infra-template.yml"
FILTER_DEFINITIONS="$CONFIG_DIR/filter-definitions.yml"

# Check if template exists
if [ ! -f "$TEMPLATE_FILE" ]; then
  echo "Error: Template file $TEMPLATE_FILE not found!"
  exit 1
fi

# Check if filter definitions exist
if [ ! -f "$FILTER_DEFINITIONS" ]; then
  echo "Error: Filter definitions file $FILTER_DEFINITIONS not found!"
  exit 1
fi

# Generate configurations for each filter type
generate_config() {
  local filter_type=$1
  local output_file="$CONFIG_DIR/newrelic-infra-$filter_type.yml"
  local sample_rate=${2:-60}
  local collect_cmdline=${3:-false}
  
  echo "Generating $output_file with sample rate $sample_rate..."
  
  # Start with template content
  cat "$TEMPLATE_FILE" > "$output_file"
  
  # Set sample rate
  sed -i "s/metrics_process_sample_rate:.*/metrics_process_sample_rate: $sample_rate/g" "$output_file"
  
  # Set command line collection
  if [ "$collect_cmdline" = "true" ]; then
    sed -i "s/collect_command_line:.*/collect_command_line: true/g" "$output_file"
  else
    sed -i "s/collect_command_line:.*/collect_command_line: false/g" "$output_file"
  fi
  
  # Apply filter definitions
  case "$filter_type" in
    none)
      # Remove all process filtering
      sed -i '/exclude_matching_metrics:/,/^[^ ]/{//!d}' "$output_file"
      sed -i 's/exclude_matching_metrics:.*/exclude_matching_metrics: {}/g' "$output_file"
      ;;
    
    standard)
      # Extract standard filter section from definitions
      awk '/# STANDARD FILTER START/,/# STANDARD FILTER END/' "$FILTER_DEFINITIONS" | grep -v "#" >> "$output_file"
      ;;
    
    aggressive)
      # Extract aggressive filter section from definitions
      awk '/# AGGRESSIVE FILTER START/,/# AGGRESSIVE FILTER END/' "$FILTER_DEFINITIONS" | grep -v "#" >> "$output_file"
      ;;
    
    targeted)
      # Extract targeted filter section from definitions
      awk '/# TARGETED FILTER START/,/# TARGETED FILTER END/' "$FILTER_DEFINITIONS" | grep -v "#" >> "$output_file"
      ;;
    
    *)
      echo "Unknown filter type: $filter_type"
      exit 1
      ;;
  esac
  
  echo "Generated $output_file"
}

# Generate configurations for all filter types
generate_config "none" 60 false
generate_config "standard" 60 false
generate_config "aggressive" 60 false
generate_config "targeted" 60 false

echo "Configuration generation complete."
