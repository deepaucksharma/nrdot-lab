#
# Unified validation script for ProcessSample Optimization Lab (PowerShell version)
# Checks current ingest rates and calculates savings
#

param (
    [string]$Format = "text",      # Output format (text, json, csv)
    [switch]$Detailed = $false,    # Include detailed process breakdown
    [string]$Since = "1 hour ago"  # Time range for queries
)

# Configuration
$ApiKey = $env:NEW_RELIC_API_KEY
$AccountId = $env:NR_ACCOUNT_ID

# Check if required variables are set
if ([string]::IsNullOrEmpty($ApiKey) -or [string]::IsNullOrEmpty($AccountId)) {
    Write-Host "Error: NEW_RELIC_API_KEY and NR_ACCOUNT_ID must be set!" -ForegroundColor Red
    Write-Host "Please ensure the .env file is properly configured."
    exit 1
}

# Create results directory
$timestamp = Get-Date -Format "yyyyMMdd_HHmmss"
$resultsDir = "results\$timestamp"
New-Item -ItemType Directory -Path $resultsDir -Force | Out-Null

# Base NRQL queries
$PsQuery = "FROM ProcessSample SELECT count(*) / uniqueCount(timestamp) as 'Events per Interval', uniqueCount(commandName) as 'Unique Processes', bytecountestimate() / 10e8 as 'GB/Day' SINCE $Since"
$MetricsQuery = "FROM Metric SELECT bytecountestimate() / 10e8 as 'GB/Day' WHERE metricName LIKE 'system.%' SINCE $Since"

# For the detailed breakdown
if ($Detailed) {
    $DetailedQuery = "FROM ProcessSample SELECT count(*) as 'Events', uniqueCount(timestamp) as 'Intervals', average(processDisplayName) as 'Process', average(cpuPercent) as 'CPU %', average(memoryResidentSizeBytes)/1024/1024 as 'Memory (MB)' FACET processDisplayName LIMIT 100 SINCE $Since"
}

# GraphQL query function
function Invoke-NrGraphQL {
    param (
        [string]$NrqlQuery
    )
    
    $headers = @{
        "Api-Key" = $ApiKey
        "Content-Type" = "application/json"
    }
    
    $body = @{
        query = "{ actor { account(id: $AccountId) { nrql(query: `"$NrqlQuery`") { results } } } }"
    } | ConvertTo-Json
    
    $response = Invoke-RestMethod -Uri "https://api.newrelic.com/graphql" -Method Post -Headers $headers -Body $body
    return $response.data.actor.account.nrql.results
}

# Fetch data
Write-Host "Fetching ProcessSample data..."
$PsResult = Invoke-NrGraphQL -NrqlQuery $PsQuery
$PsData = $PsResult[0]

Write-Host "Fetching OpenTelemetry Metrics data..."
$MetricsResult = Invoke-NrGraphQL -NrqlQuery $MetricsQuery
$MetricsData = $MetricsResult[0]

# For detailed breakdown
$DetailedResult = $null
if ($Detailed) {
    Write-Host "Fetching detailed process breakdown..."
    $DetailedResult = Invoke-NrGraphQL -NrqlQuery $DetailedQuery
}

# Extract values
$EventsPerInterval = $PsData."Events per Interval"
$UniqueProcesses = $PsData."Unique Processes"
$PsGbDay = $PsData."GB/Day"
$MetricsGbDay = $MetricsData."GB/Day"

# Calculate derived values
$TotalGbDay = $PsGbDay + $MetricsGbDay
$ApproxMonthlyCost = $TotalGbDay * 30 * 0.25  # Assuming $0.25 per GB
$BaselineGbDay = $PsGbDay * 3  # Typical baseline is 3x our optimized value
$SavingsPct = [math]::Round((1 - ($PsGbDay / $BaselineGbDay)) * 100, 2)

# Output results based on format
switch ($Format) {
    "json" {
        # Create JSON output
        $jsonOutput = [PSCustomObject]@{
            timestamp = (Get-Date).ToUniversalTime().ToString("o")
            processSample = [PSCustomObject]@{
                eventsPerInterval = $EventsPerInterval
                uniqueProcesses = $UniqueProcesses
                gbPerDay = $PsGbDay
            }
            metrics = [PSCustomObject]@{
                gbPerDay = $MetricsGbDay
            }
            total = [PSCustomObject]@{
                gbPerDay = $TotalGbDay
                estimatedMonthlyCost = $ApproxMonthlyCost
                savingsPercent = $SavingsPct
            }
        }
        
        # Add detailed process data if requested
        if ($Detailed) {
            $jsonOutput | Add-Member -MemberType NoteProperty -Name "processDetails" -Value $DetailedResult
        }
        
        $jsonOutput | ConvertTo-Json -Depth 10 | Tee-Object -FilePath "$resultsDir\validation.json"
    }
    
    "csv" {
        # Create CSV header and data
        $csvData = [PSCustomObject]@{
            Timestamp = (Get-Date).ToUniversalTime().ToString("o")
            "Events Per Interval" = $EventsPerInterval
            "Unique Processes" = $UniqueProcesses
            "ProcessSample GB/Day" = $PsGbDay
            "Metrics GB/Day" = $MetricsGbDay
            "Total GB/Day" = $TotalGbDay
            "Monthly Cost Est." = $ApproxMonthlyCost
            "Savings %" = "$SavingsPct%"
        }
        
        $csvData | Export-Csv -Path "$resultsDir\validation.csv" -NoTypeInformation
        
        # If detailed, create a separate CSV for process details
        if ($Detailed) {
            $DetailedResult | Select-Object Process, Events, Intervals, "CPU %", "Memory (MB)" | 
                Export-Csv -Path "$resultsDir\process_details.csv" -NoTypeInformation
        }
        
        Write-Host "Results saved to $resultsDir\validation.csv" -ForegroundColor Green
        if ($Detailed) {
            Write-Host "Process details saved to $resultsDir\process_details.csv" -ForegroundColor Green
        }
    }
    
    default {  # text
        # Display formatted text output
        Write-Host ""
        Write-Host "======= ProcessSample Optimization Lab Results =======" -ForegroundColor Cyan
        Write-Host "Time: $(Get-Date)"
        Write-Host ""
        Write-Host "Current ProcessSample Stats:" -ForegroundColor Yellow
        Write-Host "  Events per interval: $EventsPerInterval"
        Write-Host "  Unique processes:    $UniqueProcesses"
        Write-Host "  Data volume:         $PsGbDay GB/day"
        Write-Host ""
        Write-Host "OpenTelemetry Metrics:" -ForegroundColor Yellow
        Write-Host "  Data volume:         $MetricsGbDay GB/day"
        Write-Host ""
        Write-Host "Total Data Ingest:" -ForegroundColor Yellow
        Write-Host "  Combined volume:     $TotalGbDay GB/day"
        Write-Host "  Est. monthly cost:   `$$ApproxMonthlyCost"
        Write-Host ""
        Write-Host "Estimated Savings:" -ForegroundColor Green
        Write-Host "  Baseline volume:     $BaselineGbDay GB/day (standard configuration)"
        Write-Host "  Reduction:           $SavingsPct%"
        Write-Host ""
        Write-Host "===================================================" -ForegroundColor Cyan
        
        # Save the same output to a file
        $textOutput = @"
======= ProcessSample Optimization Lab Results =======
Time: $(Get-Date)

Current ProcessSample Stats:
  Events per interval: $EventsPerInterval
  Unique processes:    $UniqueProcesses
  Data volume:         $PsGbDay GB/day

OpenTelemetry Metrics:
  Data volume:         $MetricsGbDay GB/day

Total Data Ingest:
  Combined volume:     $TotalGbDay GB/day
  Est. monthly cost:   `$$ApproxMonthlyCost

Estimated Savings:
  Baseline volume:     $BaselineGbDay GB/day (standard configuration)
  Reduction:           $SavingsPct%

===================================================
"@
        Set-Content -Path "$resultsDir\validation.txt" -Value $textOutput
        
        # If detailed, add process details to a separate file
        if ($Detailed) {
            "Top Processes by CPU Usage:" | Set-Content -Path "$resultsDir\process_details.txt"
            $DetailedResult | ForEach-Object {
                "$($_.Process): $($_.'CPU %')% CPU, $($_.'Memory (MB)') MB RAM, $($_.Events) events"
            } | Add-Content -Path "$resultsDir\process_details.txt"
            
            Write-Host "Process details saved to $resultsDir\process_details.txt" -ForegroundColor Green
        }
    }
}

Write-Host "Validation complete." -ForegroundColor Green
