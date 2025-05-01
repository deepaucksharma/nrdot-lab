#!/usr/bin/env bash
set -e

# Script to generate detailed reports from NRDB using NRQL queries
# Requires valid NEW_RELIC_API_KEY and NR_ACCOUNT_ID in .env

RESULTS_DIR="./results"
TIMESTAMP=$(date +%Y%m%d_%H%M%S)
REPORT_DIR="${RESULTS_DIR}/${TIMESTAMP}_nrdb_report"

# Load environment variables
source .env

# Check for required environment variables
if [[ -z "$NEW_RELIC_API_KEY" || -z "$NR_ACCOUNT_ID" ]]; then
  echo "❌ NEW_RELIC_API_KEY or NR_ACCOUNT_ID missing"
  exit 1
fi

# Create report directory
mkdir -p "${REPORT_DIR}"

echo "🔍 Generating detailed NRDB report..."

# Function to run NRQL query and save results
run_query() {
  local name=$1
  local query=$2
  local description=$3
  
  echo "Running query: ${name}..."
  
  # Prepare GraphQL query
  read -r -d '' GRAPHQL_QUERY <<EOF
{
  actor {
    account(id: ${NR_ACCOUNT_ID}) {
      nrql(query: "${query}") {
        results
      }
    }
  }
}
EOF

  # Execute query
  local payload=$(echo "${GRAPHQL_QUERY}" | jq -R -s '{query: .}')
  local response=$(curl -s -X POST https://api.newrelic.com/graphql \
    -H "Content-Type: application/json" \
    -H "API-Key: ${NEW_RELIC_API_KEY}" \
    -d "${payload}")
  
  # Save raw JSON response
  echo "${response}" > "${REPORT_DIR}/${name}_raw.json"
  
  # Extract results
  local results=$(echo "${response}" | jq -r '.data.actor.account.nrql.results')
  
  # Save formatted results
  echo "# ${name}" > "${REPORT_DIR}/${name}.md"
  echo "" >> "${REPORT_DIR}/${name}.md"
  echo "${description}" >> "${REPORT_DIR}/${name}.md"
  echo "" >> "${REPORT_DIR}/${name}.md"
  echo '```json' >> "${REPORT_DIR}/${name}.md"
  echo "${results}" >> "${REPORT_DIR}/${name}.md"
  echo '```' >> "${REPORT_DIR}/${name}.md"
  
  echo "✅ Query ${name} completed"
}

# Define NRQL queries for analysis
QUERIES=(
  "volume_by_time:SELECT bytecountestimate()/1e9 as 'GB' FROM ProcessSample TIMESERIES 5 minutes SINCE 1 hour ago:ProcessSample ingest volume over time (5-minute intervals)"
  "volume_by_host:SELECT bytecountestimate()/1e9 as 'GB' FROM ProcessSample FACET entityName LIMIT 10 SINCE 1 hour ago:ProcessSample ingest volume by host"
  "volume_by_process:SELECT bytecountestimate()/1e9 as 'GB' FROM ProcessSample FACET processDisplayName LIMIT 20 SINCE 1 hour ago:ProcessSample ingest volume by process name"
  "event_count:SELECT count(*) as 'Events' FROM ProcessSample TIMESERIES 5 minutes SINCE 1 hour ago:ProcessSample event count over time"
  "avg_event_size:SELECT bytecountestimate()/count(*) as 'Bytes per Event' FROM ProcessSample SINCE 1 hour ago:Average ProcessSample event size"
  "cpu_usage:SELECT average(cpuPercent) as 'CPU %' FROM ProcessSample FACET processDisplayName LIMIT 10 SINCE 1 hour ago:Top processes by CPU usage"
  "memory_usage:SELECT average(memoryResidentSizeBytes)/1024/1024 as 'Memory (MB)' FROM ProcessSample FACET processDisplayName LIMIT 10 SINCE 1 hour ago:Top processes by memory usage"
)

# Run all queries
for query_spec in "${QUERIES[@]}"; do
  IFS=':' read -r name query description <<< "${query_spec}"
  run_query "${name}" "${query}" "${description}"
done

# Generate summary report
echo "📊 Creating summary report..."

cat > "${REPORT_DIR}/summary.md" << EOF
# New Relic ProcessSample Optimization Analysis

## Overview
This report contains detailed metrics from New Relic, analyzing ProcessSample data over the past hour.

## Key Metrics

### Total Ingest Volume
EOF

# Extract total ingest volume
TOTAL_GB=$(jq -r '.[0]."GB"' "${REPORT_DIR}/avg_event_size_raw.json" 2>/dev/null || echo "N/A")
echo "Total ProcessSample ingest: **${TOTAL_GB} GB** over the past hour" >> "${REPORT_DIR}/summary.md"

# Add event count
EVENT_COUNT=$(jq -r 'reduce .[] as $item (0; . + $item."Events")' "${REPORT_DIR}/event_count_raw.json" 2>/dev/null || echo "N/A")
echo "Total events: **${EVENT_COUNT}** over the past hour" >> "${REPORT_DIR}/summary.md"

# Add average event size
AVG_SIZE=$(jq -r '.[0]."Bytes per Event"' "${REPORT_DIR}/avg_event_size_raw.json" 2>/dev/null || echo "N/A")
echo "Average event size: **${AVG_SIZE} bytes**" >> "${REPORT_DIR}/summary.md"

# Add section for top processes
cat >> "${REPORT_DIR}/summary.md" << EOF

## Top Processes by Ingest Volume
EOF

# Extract top 5 processes by volume
TOP_PROCESSES=$(jq -r '.[] | select(."GB" != null) | "\(.processDisplayName): \(."GB") GB"' "${REPORT_DIR}/volume_by_process_raw.json" 2>/dev/null | head -5)
if [[ -n "${TOP_PROCESSES}" ]]; then
  echo "${TOP_PROCESSES}" | while read line; do
    echo "- ${line}" >> "${REPORT_DIR}/summary.md"
  done
else
  echo "- No data available" >> "${REPORT_DIR}/summary.md"
fi

# Generate recommendations
cat >> "${REPORT_DIR}/summary.md" << EOF

## Optimization Recommendations

Based on the data collected, here are some recommendations to further optimize ProcessSample ingest:

1. **Increase sampling interval**: The current configuration shows significant reduction compared to the default 20s interval.

2. **Process-specific filtering**: Consider adding explicit filters for high-volume, low-value processes.

3. **Command line exclusion**: Ensure command line collection is disabled to reduce event size.

4. **Host targeting**: Focus optimization on hosts with highest ingest volume first.

## Next Steps

1. Compare these results with baseline measurements to quantify savings.
2. Run the optimization lab with different scenarios to find the optimal configuration.
3. Implement the optimized configuration in your production environment.
EOF

echo "🎉 NRDB report generation complete!"
echo "📋 Report location: ${REPORT_DIR}/summary.md"
