#!/usr/bin/env bash
# A simplified validation script that doesn't require jq
# Usage: ./scripts/validate_simple.sh

set -e

if [[ -z $NEW_RELIC_API_KEY || -z $NR_ACCOUNT_ID ]]; then
  echo "⚠️  Environment variables missing. Make sure to load .env variables first:"
  echo "    source .env"
  exit 1
fi

echo "🔍 Querying New Relic API for ProcessSample ingest volume (last 30 minutes)..."

# Create a simplified query without jq
QUERY="{\"query\":\"{actor {account(id: $NR_ACCOUNT_ID) {nrql(query: \\\"SELECT bytecountestimate()/1e9 FROM ProcessSample SINCE 30 MINUTES AGO\\\") {results}}}}\"}"

# Send the request to New Relic API
RESPONSE=$(curl -s -H "API-Key: $NEW_RELIC_API_KEY" \
                -H "Content-Type: application/json" \
                -d "$QUERY" \
                --fail-with-body https://api.newrelic.com/graphql || echo "{\"errors\":[{\"message\":\"API call failed\"}]}")

# Check for errors in the response
if echo "$RESPONSE" | grep -q "errors"; then
  ERROR_MSG=$(echo "$RESPONSE" | grep -o '"message":"[^"]*"' | head -1 | cut -d'"' -f4)
  echo "❌ Error: $ERROR_MSG"
  exit 1
fi

# Simple extraction with grep and sed
GB=$(echo "$RESPONSE" | grep -o '"results":\[\[[0-9.]*\]\]' | sed 's/"results":\[\[//g' | sed 's/\]\]//g')

if [[ -z $GB ]]; then
  echo "⚠️  No ProcessSample data found in the last 30 minutes"
  GB="N/A"
else
  GB_FORMATTED=$(printf "%.3f" $GB)
  echo "📊 ProcessSample ingest (last 30 min): $GB_FORMATTED GB"
fi

# Calculate cost estimate if we have valid data
if [[ $GB != "N/A" ]]; then
  # Assuming $0.30 per GB for ingest pricing
  MONTHLY_ESTIMATE=$(echo "$GB * 24 * 30 / 0.5 * 0.30" | bc -l)
  MONTHLY_FORMATTED=$(printf "%.2f" $MONTHLY_ESTIMATE)
  echo "💰 Estimated monthly cost: \$$MONTHLY_FORMATTED (based on \$0.30/GB)"
fi
