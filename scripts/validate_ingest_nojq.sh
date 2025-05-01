#!/usr/bin/env bash
set -eo pipefail

[[ -z $NEW_RELIC_API_KEY || -z $NR_ACCOUNT_ID ]] && {
  echo "❌ NEW_RELIC_API_KEY or NR_ACCOUNT_ID missing"; exit 1; }

# Create the GraphQL query
QUERY="{\"query\":\"{actor {account(id: $NR_ACCOUNT_ID) {nrql(query: \\\"SELECT bytecountestimate(estimate)/1e9 FROM ProcessSample SINCE 30 MINUTES AGO\\\") {results}}}}\"}"

# Send the request to New Relic API
resp=$(curl -sS -H "API-Key: $NEW_RELIC_API_KEY" \
             -H "Content-Type: application/json" \
             -d "$QUERY" --fail https://api.newrelic.com/graphql)

# Extract the result using grep and sed instead of jq
# This is a simplified extraction and might need adjustment based on the actual response format
gb=$(echo "$resp" | grep -o '"results":\[\[.*\]\]' | sed 's/"results":\[\[//g' | sed 's/\]\]//g')

echo "ProcessSample ingest (last 30 min): ${gb:-N/A} GB"
