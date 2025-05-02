# PowerShell version of validate_ingest.sh
param (
    [int]$TIME_WINDOW = 30,
    [switch]$DETAILED,
    [switch]$OUTPUT_JSON
)

# Check for required environment variables
if (-not $env:NEW_RELIC_API_KEY -or -not $env:NR_ACCOUNT_ID) {
    Write-Error "❌ NEW_RELIC_API_KEY or NR_ACCOUNT_ID missing"
    exit 1
}

$GB_COST = if ($env:GB_COST) { $env:GB_COST } else { 0.30 }
$BASELINE_RATE = if ($env:BASELINE_RATE) { $env:BASELINE_RATE } else { 20 }
$CURRENT_RATE = if ($env:CURRENT_RATE) { $env:CURRENT_RATE } else { 60 }

# NerdGraph query for ProcessSample data
$query = @"
{
  actor { account(id: $env:NR_ACCOUNT_ID) {
      nrql(query: "SELECT bytecountestimate()/1e9 FROM ProcessSample SINCE $TIME_WINDOW MINUTES AGO") { results }
  }}
}
"@

$payload = @{
    query = $query
} | ConvertTo-Json

# Make API request
$response = Invoke-RestMethod -Uri "https://api.newrelic.com/graphql" `
                            -Method Post `
                            -Headers @{
                                "Content-Type" = "application/json"
                                "API-Key" = $env:NEW_RELIC_API_KEY
                            } `
                            -Body $payload

# Extract GB value
$gb = $response.data.actor.account.nrql.results[0].'bytecountestimate()/1e9'

if (-not $gb) {
    Write-Host "No ProcessSample data found in the last $TIME_WINDOW minutes."
    exit 0
}

# Calculate daily and monthly estimates
$daily_gb = $gb * 24 * 60 / $TIME_WINDOW
$monthly_gb = $daily_gb * 30
$monthly_cost = $monthly_gb * $GB_COST

# Calculate the reduction percentage compared to baseline
$baseline_factor = $CURRENT_RATE / $BASELINE_RATE
$baseline_gb = $monthly_gb * $baseline_factor
$reduction = (1 - ($monthly_gb / $baseline_gb)) * 100

# Get process-level breakdowns if detailed output is requested
$process_details = $null
if ($DETAILED) {
    $detail_query = @"
    {
      actor { account(id: $env:NR_ACCOUNT_ID) {
          nrql(query: "SELECT bytecountestimate()/1e9 as GB FROM ProcessSample FACET processDisplayName LIMIT 10 SINCE $TIME_WINDOW MINUTES AGO") { results }
      }}
    }
"@
    
    $detail_payload = @{
        query = $detail_query
    } | ConvertTo-Json
    
    $detail_response = Invoke-RestMethod -Uri "https://api.newrelic.com/graphql" `
                                      -Method Post `
                                      -Headers @{
                                          "Content-Type" = "application/json"
                                          "API-Key" = $env:NEW_RELIC_API_KEY
                                      } `
                                      -Body $detail_payload
    
    $process_details = $detail_response.data.actor.account.nrql.results
}

# Output results
if ($OUTPUT_JSON) {
    # JSON output for CI/automation
    $json_output = @{
        time_window = "$TIME_WINDOW"
        gb = "$gb"
        daily_gb = "$daily_gb"
        monthly_gb = "$monthly_gb"
        monthly_cost = "$monthly_cost"
        reduction_percent = "$reduction"
        baseline_rate = "$BASELINE_RATE"
        current_rate = "$CURRENT_RATE"
    } | ConvertTo-Json
    
    Write-Output $json_output
} else {
    # Human-readable output
    Write-Host ""
    Write-Host "RESULTS:"
    Write-Host "--------------------------"
    Write-Host "Time window: $TIME_WINDOW minutes"
    Write-Host "ProcessSample volume: $gb GB"
    Write-Host "Estimated GB/day: $([math]::Round($daily_gb, 2))"
    Write-Host "Estimated GB/month: $([math]::Round($monthly_gb, 2))"
    Write-Host "Estimated monthly cost: `$$([math]::Round($monthly_cost, 2))"
    Write-Host "Reduction vs baseline (${BASELINE_RATE}s): $([math]::Round($reduction, 2))%"
    Write-Host "--------------------------"
    
    # If detailed was requested, show process-level breakdown
    if ($DETAILED -and $process_details) {
        Write-Host ""
        Write-Host "TOP PROCESSES BY VOLUME:"
        Write-Host "--------------------------"
        foreach ($process in $process_details) {
            Write-Host "$($process.processDisplayName): $($process.GB) GB"
        }
        Write-Host "--------------------------"
    }
}
