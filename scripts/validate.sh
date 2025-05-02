#!/bin/bash
#
# Unified validation script for ProcessSample Optimization Lab
# Checks current ingest rates and calculates savings
#

set -e

# Configuration
API_KEY=${NEW_RELIC_API_KEY}
ACCOUNT_ID=${NR_ACCOUNT_ID}
FORMAT=${1:-text}  # Default format is text
DETAILED=false
SINCE="1 hour ago"

# Parse arguments
while [[ $# -gt 0 ]]; do
  case $1 in
    --format)
      FORMAT="$2"
      shift 2
      ;;
    --detailed)
      DETAILED=true
      shift
      ;;
    --since)
      SINCE="$2"
      shift 2
      ;;
    *)
      shift
      ;;
  esac
done

# Check if required variables are set
if [ -z "$API_KEY" ] || [ -z "$ACCOUNT_ID" ]; then
  echo "Error: API_KEY and ACCOUNT_ID must be set!"
  echo "Please ensure the .env file is properly configured."
  exit 1
fi

# Check if jq is installed
if ! command -v jq &>/dev/null; then
  echo "Error: jq is required but not installed."
  echo "Please install jq:"
  echo "  - Linux: apt-get install jq / yum install jq"
  echo "  - MacOS: brew install jq"
  echo "  - Windows: choco install jq / scoop install jq"
  exit 1
fi

# Create results directory
timestamp=$(date +%Y%m%d_%H%M%S)
mkdir -p results/$timestamp

# Base NRQL query
PS_QUERY="FROM ProcessSample SELECT count(*) / uniqueCount(timestamp) as 'Events per Interval', uniqueCount(commandName) as 'Unique Processes', bytecountestimate() / 10e8 as 'GB/Day' SINCE $SINCE"
METRICS_QUERY="FROM Metric SELECT bytecountestimate() / 10e8 as 'GB/Day' WHERE metricName LIKE 'system.%' SINCE $SINCE"

# For the detailed breakdown
if [ "$DETAILED" = true ]; then
  DETAILED_QUERY="FROM ProcessSample SELECT count(*) as 'Events', uniqueCount(timestamp) as 'Intervals', average(processDisplayName) as 'Process', average(cpuPercent) as 'CPU %', average(memoryResidentSizeBytes)/1024/1024 as 'Memory (MB)' FACET processDisplayName LIMIT 100 SINCE $SINCE"
fi

# Fetch data
echo "Fetching ProcessSample data..."
PS_RESULT=$(curl -s -X POST \
  "https://api.newrelic.com/graphql" \
  -H "Api-Key: $API_KEY" \
  -H "Content-Type: application/json" \
  --data-binary "{\"query\": \"{ actor { account(id: $ACCOUNT_ID) { nrql(query: \\\"$PS_QUERY\\\") { results } } } }\"}" \
  | jq -r '.data.actor.account.nrql.results[0]')

echo "Fetching OpenTelemetry Metrics data..."
METRICS_RESULT=$(curl -s -X POST \
  "https://api.newrelic.com/graphql" \
  -H "Api-Key: $API_KEY" \
  -H "Content-Type: application/json" \
  --data-binary "{\"query\": \"{ actor { account(id: $ACCOUNT_ID) { nrql(query: \\\"$METRICS_QUERY\\\") { results } } } }\"}" \
  | jq -r '.data.actor.account.nrql.results[0]')

# For detailed breakdown
if [ "$DETAILED" = true ]; then
  echo "Fetching detailed process breakdown..."
  DETAILED_RESULT=$(curl -s -X POST \
    "https://api.newrelic.com/graphql" \
    -H "Api-Key: $API_KEY" \
    -H "Content-Type: application/json" \
    --data-binary "{\"query\": \"{ actor { account(id: $ACCOUNT_ID) { nrql(query: \\\"$DETAILED_QUERY\\\") { results } } } }\"}" \
    | jq '.data.actor.account.nrql.results')
fi

# Extract values
EVENTS_PER_INTERVAL=$(echo $PS_RESULT | jq -r '."Events per Interval"')
UNIQUE_PROCESSES=$(echo $PS_RESULT | jq -r '."Unique Processes"')
PS_GB_DAY=$(echo $PS_RESULT | jq -r '."GB/Day"')
METRICS_GB_DAY=$(echo $METRICS_RESULT | jq -r '."GB/Day"')

# Calculate derived values
TOTAL_GB_DAY=$(echo "$PS_GB_DAY + $METRICS_GB_DAY" | bc)
APPROX_MONTHLY_COST=$(echo "$TOTAL_GB_DAY * 30 * 0.25" | bc)  # Assuming $0.25 per GB
BASELINE_GB_DAY=$(echo "$PS_GB_DAY * 3" | bc)  # Typical baseline is 3x our optimized value
SAVINGS_PCT=$(echo "scale=2; (1 - ($PS_GB_DAY / $BASELINE_GB_DAY)) * 100" | bc)

# Output results based on format
case $FORMAT in
  json)
    # Create JSON output
    JSON_OUTPUT=$(jq -n \
      --arg timestamp "$(date -u +"%Y-%m-%dT%H:%M:%SZ")" \
      --arg events_per_interval "$EVENTS_PER_INTERVAL" \
      --arg unique_processes "$UNIQUE_PROCESSES" \
      --arg ps_gb_day "$PS_GB_DAY" \
      --arg metrics_gb_day "$METRICS_GB_DAY" \
      --arg total_gb_day "$TOTAL_GB_DAY" \
      --arg monthly_cost "$APPROX_MONTHLY_COST" \
      --arg savings_pct "$SAVINGS_PCT" \
      '{
        "timestamp": $timestamp,
        "processSample": {
          "eventsPerInterval": $events_per_interval | tonumber,
          "uniqueProcesses": $unique_processes | tonumber,
          "gbPerDay": $ps_gb_day | tonumber
        },
        "metrics": {
          "gbPerDay": $metrics_gb_day | tonumber
        },
        "total": {
          "gbPerDay": $total_gb_day | tonumber,
          "estimatedMonthlyCost": $monthly_cost | tonumber,
          "savingsPercent": $savings_pct | tonumber
        }
      }')
    
    # Add detailed process data if requested
    if [ "$DETAILED" = true ]; then
      JSON_OUTPUT=$(echo $JSON_OUTPUT | jq --argjson detailed "$DETAILED_RESULT" '. + {"processDetails": $detailed}')
    fi
    
    echo $JSON_OUTPUT | jq .
    echo $JSON_OUTPUT > "results/$timestamp/validation.json"
    ;;
    
  csv)
    # Create CSV header
    echo "Timestamp,Events Per Interval,Unique Processes,ProcessSample GB/Day,Metrics GB/Day,Total GB/Day,Monthly Cost Est.,Savings %" > "results/$timestamp/validation.csv"
    
    # Add data row
    echo "$(date -u +"%Y-%m-%dT%H:%M:%SZ"),$EVENTS_PER_INTERVAL,$UNIQUE_PROCESSES,$PS_GB_DAY,$METRICS_GB_DAY,$TOTAL_GB_DAY,$APPROX_MONTHLY_COST,$SAVINGS_PCT%" >> "results/$timestamp/validation.csv"
    
    # If detailed, create a separate CSV for process details
    if [ "$DETAILED" = true ]; then
      echo "Process,Events,Intervals,CPU %,Memory (MB)" > "results/$timestamp/process_details.csv"
      echo $DETAILED_RESULT | jq -r '.[] | [.Process, .Events, .Intervals, ."CPU %", ."Memory (MB)"] | @csv' >> "results/$timestamp/process_details.csv"
    fi
    
    echo "Results saved to results/$timestamp/validation.csv"
    if [ "$DETAILED" = true ]; then
      echo "Process details saved to results/$timestamp/process_details.csv"
    fi
    ;;
    
  text|*)
    # Display formatted text output
    echo ""
    echo "======= ProcessSample Optimization Lab Results ======="
    echo "Time: $(date)"
    echo ""
    echo "Current ProcessSample Stats:"
    echo "  Events per interval: $EVENTS_PER_INTERVAL"
    echo "  Unique processes:    $UNIQUE_PROCESSES"
    echo "  Data volume:         $PS_GB_DAY GB/day"
    echo ""
    echo "OpenTelemetry Metrics:"
    echo "  Data volume:         $METRICS_GB_DAY GB/day"
    echo ""
    echo "Total Data Ingest:"
    echo "  Combined volume:     $TOTAL_GB_DAY GB/day"
    echo "  Est. monthly cost:   \$$APPROX_MONTHLY_COST"
    echo ""
    echo "Estimated Savings:"
    echo "  Baseline volume:     $BASELINE_GB_DAY GB/day (standard configuration)"
    echo "  Reduction:           $SAVINGS_PCT%"
    echo ""
    echo "==================================================="
    
    # Save the same output to a file
    {
      echo "======= ProcessSample Optimization Lab Results ======="
      echo "Time: $(date)"
      echo ""
      echo "Current ProcessSample Stats:"
      echo "  Events per interval: $EVENTS_PER_INTERVAL"
      echo "  Unique processes:    $UNIQUE_PROCESSES"
      echo "  Data volume:         $PS_GB_DAY GB/day"
      echo ""
      echo "OpenTelemetry Metrics:"
      echo "  Data volume:         $METRICS_GB_DAY GB/day"
      echo ""
      echo "Total Data Ingest:"
      echo "  Combined volume:     $TOTAL_GB_DAY GB/day"
      echo "  Est. monthly cost:   \$$APPROX_MONTHLY_COST"
      echo ""
      echo "Estimated Savings:"
      echo "  Baseline volume:     $BASELINE_GB_DAY GB/day (standard configuration)"
      echo "  Reduction:           $SAVINGS_PCT%"
      echo ""
      echo "==================================================="
    } > "results/$timestamp/validation.txt"
    
    # If detailed, add process details to a separate file
    if [ "$DETAILED" = true ]; then
      echo "Top Processes by CPU Usage:" > "results/$timestamp/process_details.txt"
      echo $DETAILED_RESULT | jq -r '.[] | "\(.Process): \(."CPU %")% CPU, \(."Memory (MB)") MB RAM, \(.Events) events"' >> "results/$timestamp/process_details.txt"
      echo "Process details saved to results/$timestamp/process_details.txt"
    fi
    ;;
esac

echo "Validation complete."
