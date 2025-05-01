#!/usr/bin/env bash
set -eo pipefail

command -v jq >/dev/null || { echo "❌ jq not installed"; exit 1; }
[[ -z $NEW_RELIC_API_KEY || -z $NR_ACCOUNT_ID ]] && {
  echo "❌ NEW_RELIC_API_KEY or NR_ACCOUNT_ID missing"; exit 1; }

TIME_WINDOW=${1:-30}
GB_COST=${GB_COST:-0.30}
BASELINE_RATE=${BASELINE_RATE:-20}  # Default baseline rate is 20s
CURRENT_RATE=${CURRENT_RATE:-60}    # Default current rate is 60s

# Output format control
OUTPUT_JSON=${OUTPUT_JSON:-false}
DETAILED=${DETAILED:-false}

read -r -d '' QUERY <<'GQL'
{
  actor { account(id: NRID) {
      nrql(query: "SELECT bytecountestimate()/1e9 FROM ProcessSample SINCE MINUTES SINCE_MIN AGO") { results }
  }}
}
GQL
QUERY=${QUERY//SINCE_MIN/$TIME_WINDOW}
payload=$(jq -Rs --arg q "${QUERY//NRID/$NR_ACCOUNT_ID}" '{query:$q}')

resp=$(curl -sS -H "API-Key: $NEW_RELIC_API_KEY" \
             -H "Content-Type: application/json" \
             -d "$payload" --fail https://api.newrelic.com/graphql)

gb=$(jq -r '.data.actor.account.nrql.results[0][]' <<<"$resp")

if [[ -z $gb || $gb == "null" ]]; then
  echo "No ProcessSample data found in the last $TIME_WINDOW minutes."
  exit 0
fi

# Calculate daily and monthly estimates
daily_gb=$(echo "$gb * 24 * 60 / $TIME_WINDOW" | bc -l)
monthly_gb=$(echo "$daily_gb * 30" | bc -l)
monthly_cost=$(echo "$monthly_gb * $GB_COST" | bc -l)

# Calculate the reduction percentage compared to baseline
baseline_factor=$(echo "scale=2; $CURRENT_RATE / $BASELINE_RATE" | bc -l)
baseline_gb=$(echo "$monthly_gb * $baseline_factor" | bc -l)
reduction=$(echo "scale=2; (1 - ($monthly_gb / $baseline_gb)) * 100" | bc -l)

# If detailed output is requested and we have data, get process-level breakdowns
if [ "$DETAILED" = "true" ]; then
  read -r -d '' DETAIL_QUERY <<'GQL'
  {
    actor { account(id: NRID) {
        nrql(query: "SELECT bytecountestimate()/1e9 FROM ProcessSample FACET processDisplayName LIMIT 10 SINCE MINUTES SINCE_MIN AGO") { results }
    }}
  }
  GQL
  DETAIL_QUERY=${DETAIL_QUERY//SINCE_MIN/$TIME_WINDOW}
  detail_payload=$(jq -Rs --arg q "${DETAIL_QUERY//NRID/$NR_ACCOUNT_ID}" '{query:$q}')
  
  detail_resp=$(curl -sS -H "API-Key: $NEW_RELIC_API_KEY" \
               -H "Content-Type: application/json" \
               -d "$detail_payload" --fail https://api.newrelic.com/graphql)
  
  process_details=$(jq -r '.data.actor.account.nrql.results[]' <<<"$detail_resp")
fi

# Output results
if [ "$OUTPUT_JSON" = "true" ]; then
  # JSON output for CI/automation
  json_output=$(jq -n \
    --arg time_window "$TIME_WINDOW" \
    --arg gb "$gb" \
    --arg daily_gb "$daily_gb" \
    --arg monthly_gb "$monthly_gb" \
    --arg monthly_cost "$monthly_cost" \
    --arg reduction "$reduction" \
    --arg baseline_rate "$BASELINE_RATE" \
    --arg current_rate "$CURRENT_RATE" \
    '{
      "time_window": $time_window,
      "gb": $gb,
      "daily_gb": $daily_gb,
      "monthly_gb": $monthly_gb,
      "monthly_cost": $monthly_cost,
      "reduction_percent": $reduction,
      "baseline_rate": $baseline_rate,
      "current_rate": $current_rate
    }')
  echo "$json_output"
else
  # Human-readable output
  echo ""
  echo "RESULTS:"
  echo "--------------------------"
  echo "Time window: $TIME_WINDOW minutes"
  echo "ProcessSample volume: ${gb:-N/A} GB"
  printf "Estimated GB/day: %.2f\n" "$daily_gb"
  printf "Estimated GB/month: %.2f\n" "$monthly_gb"
  printf "Estimated monthly cost: \$%.2f\n" "$monthly_cost"
  printf "Reduction vs baseline (${BASELINE_RATE}s): %.2f%%\n" "$reduction"
  echo "--------------------------"
  
  # If detailed was requested, show process-level breakdown
  if [ "$DETAILED" = "true" ] && [ -n "$process_details" ]; then
    echo ""
    echo "TOP PROCESSES BY VOLUME:"
    echo "--------------------------"
    jq -r '.[] | "\(.processDisplayName): \(.GB) GB"' <<<"$process_details"
    echo "--------------------------"
  fi
fi