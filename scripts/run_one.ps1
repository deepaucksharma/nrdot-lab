# PowerShell version of run_one.sh for Windows compatibility
param (
    [string]$SCEN = "test",
    [int]$SAMPLE = 60,
    [string]$FILTER = "yes",
    [string]$PROFILE = "default",
    [int]$DURATION = 30,
    [string]$STRESS_CPU = "2",
    [string]$STRESS_MEM = "128M",
    [string]$LOAD_STRESSOR = "",
    [string]$OTEL_INTERVAL = "",
    [string]$COLLECT_CMDLINE = "false",
    [string]$STRIP_CMDLINE = "false"
)

# Create results directory with timestamp
$TIMESTAMP = Get-Date -Format "yyyyMMdd_HHmmss"
$RESULTS_DIR = "results\${TIMESTAMP}"
New-Item -ItemType Directory -Path $RESULTS_DIR -Force | Out-Null

Write-Host "Running scenario ${SCEN} with sample rate ${SAMPLE}s for ${DURATION} minutes"

# Generate dynamic newrelic-infra.yml from template
Write-Host "Generating infrastructure config..."
$config = @"
license_key: `${NEW_RELIC_LICENSE_KEY}
enable_process_metrics: true
metrics_process_sample_rate: ${SAMPLE}
collect_process_commandline: ${COLLECT_CMDLINE}
"@

if ($STRIP_CMDLINE -eq "true") {
    $config += @"

strip_command_line: true
"@
}

if ($FILTER -eq "yes") {
    $config += @"

# Modern filtering syntax (works with agent v1.40+)
exclude_matching_metrics:
  process.name: ["systemd", "cron", "containerd", "dockerd", "sshd", "bash", "sh"]
  process.executable: ["/usr/bin/containerd", "/usr/sbin/cron", "/usr/bin/docker", "/usr/sbin/sshd"]
"@
}

Set-Content -Path "config\newrelic-infra.yml" -Value $config

# Handle OTel configuration if needed
if ($OTEL_INTERVAL -ne "") {
    Write-Host "Configuring OTel with ${OTEL_INTERVAL}s interval..."
    $otelConfig = Get-Content -Path "config\otel-config.yaml" -Raw
    $otelConfig = $otelConfig -replace "collection_interval: 10s", "collection_interval: ${OTEL_INTERVAL}s"
    Set-Content -Path "config\otel-config.yaml" -Value $otelConfig
}

# Set environment variables for the load generator
$env:STRESS_CPU = $STRESS_CPU
$env:STRESS_MEM = $STRESS_MEM
$env:LOAD_STRESSOR = $LOAD_STRESSOR

# Start containers with specified profile
Write-Host "Starting containers with profile: ${PROFILE}..."
Invoke-Expression "docker compose --profile `"${PROFILE}`" up -d"

# Wait for the specified duration
Write-Host "Running for ${DURATION} minutes..."
Start-Sleep -Seconds ($DURATION * 60)

# Capture docker stats for resource usage
Write-Host "Capturing resource metrics..."
$dockerStats = Invoke-Expression "docker stats --no-stream"
Set-Content -Path "${RESULTS_DIR}\${SCEN}_docker_stats.txt" -Value $dockerStats

# Run validation to get ingest metrics
Write-Host "Validating ingest metrics..."
$env:OUTPUT_JSON = "true"
$env:TIME_WINDOW = $DURATION
$env:BASELINE_RATE = 20
$env:CURRENT_RATE = $SAMPLE
$ingestStats = Invoke-Expression ".\scripts\validate_ingest.sh"
Set-Content -Path "${RESULTS_DIR}\${SCEN}_ingest.json" -Value $ingestStats

# Check if stress-ng container is running
$stressRunning = docker ps | Select-String -Pattern "stress-load"
if ($stressRunning) {
    Write-Host "Calculating visibility delay..."
    $VIS_DELAY = Invoke-Expression "python .\scripts\vis_latency.py"
    
    # Append visibility delay to the JSON file
    $ingestJson = Get-Content -Path "${RESULTS_DIR}\${SCEN}_ingest.json" | ConvertFrom-Json
    $ingestJson | Add-Member -NotePropertyName "visibility_delay_s" -NotePropertyValue $VIS_DELAY
    $ingestJson | ConvertTo-Json | Set-Content -Path "${RESULTS_DIR}\${SCEN}_ingest.json"
}

# Combine all metrics into a final results JSON
Write-Host "Generating final results..."
$resultJson = Get-Content -Path "${RESULTS_DIR}\${SCEN}_ingest.json" | ConvertFrom-Json
$resultJson | Add-Member -NotePropertyName "scenario_id" -NotePropertyValue $SCEN
$resultJson | Add-Member -NotePropertyName "profile" -NotePropertyValue $PROFILE
$resultJson | Add-Member -NotePropertyName "filtering" -NotePropertyValue $FILTER
$resultJson | ConvertTo-Json | Set-Content -Path "${RESULTS_DIR}\${SCEN}.json"

Write-Host "Scenario ${SCEN} completed. Results saved to ${RESULTS_DIR}\${SCEN}.json"
