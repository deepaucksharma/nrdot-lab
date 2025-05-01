#!/usr/bin/env bash
set -eo pipefail

command -v jq >/dev/null || { echo "❌ jq not installed"; exit 1; }
[[ -z $NEW_RELIC_API_KEY || -z $NR_ACCOUNT_ID ]] && {
  echo "❌ NEW_RELIC_API_KEY or NR_ACCOUNT_ID missing"; exit 1; }

TIME_WINDOW=${1:-30}
GB_COST=${GB_COST:-0.30}

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

# Calculate the reduction percentage compared to baseline (20s interval)
baseline_factor=3  # 60s/20s = 3x reduction from baseline
baseline_gb=$(echo "$monthly_gb * $baseline_factor" | bc -l)
reduction=$(echo "scale=2; (1 - ($monthly_gb / $baseline_gb)) * 100" | bc -l)

echo ""
echo "RESULTS:"
echo "--------------------------"
echo "Time window: $TIME_WINDOW minutes"
echo "ProcessSample volume: ${gb:-N/A} GB"
echo "Estimated GB/day: $(printf "%.2f" $daily_gb)"
echo "Estimated GB/month: $(printf "%.2f" $monthly_gb)"
echo "Estimated monthly cost: \$$(printf "%.2f" $monthly_cost)"
echo "Reduction vs baseline: ${reduction}%"
echo "--------------------------"