@echo off
REM Load environment variables from .env file
for /F "tokens=*" %%A in (.env) do (
    set %%A
)

REM Check if required variables are set
if "%NEW_RELIC_API_KEY%"=="" (
    echo NEW_RELIC_API_KEY is not set
    exit /b 1
)
if "%NR_ACCOUNT_ID%"=="" (
    echo NR_ACCOUNT_ID is not set
    exit /b 1
)

REM Create a temporary file for the query
echo {"query":"{actor {account(id: %NR_ACCOUNT_ID%) {nrql(query: \"SELECT bytecountestimate(estimate)/1e9 FROM ProcessSample SINCE 30 MINUTES AGO\") {results}}}}"} > query.json

REM Send the request to New Relic API
curl -s -H "API-Key: %NEW_RELIC_API_KEY%" -H "Content-Type: application/json" -d @query.json https://api.newrelic.com/graphql > response.json

REM Display the raw response for now, as we don't have jq for parsing
echo Raw response from New Relic API:
type response.json

REM Clean up temporary files
del query.json
del response.json
