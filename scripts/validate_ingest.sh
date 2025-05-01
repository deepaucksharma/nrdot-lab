#!/usr/bin/env bash
set -eo pipefail

command -v jq >/dev/null || { echo "❌ jq not installed"; exit 1; }
[[ -z $NEW_RELIC_API_KEY || -z $NR_ACCOUNT_ID ]] && {
  echo "❌ NEW_RELIC_API_KEY or NR_ACCOUNT_ID missing"; exit 1; }

read -r -d '' QUERY <<'GQL'
{
  actor { account(id: NRID) {
      nrql(query: "SELECT bytecountestimate(estimate)/1e9 FROM ProcessSample SINCE 30 MINUTES AGO") { results }
  }}
}
GQL
payload=$(jq -Rs --arg q "${QUERY//NRID/$NR_ACCOUNT_ID}" '{query:$q}')

resp=$(curl -sS -H "API-Key: $NEW_RELIC_API_KEY" \
             -H "Content-Type: application/json" \
             -d "$payload" --fail https://api.newrelic.com/graphql)

gb=$(jq -r '.data.actor.account.nrql.results[0][]' <<<"$resp")
echo "ProcessSample ingest (last 30 min): ${gb:-N/A} GB"