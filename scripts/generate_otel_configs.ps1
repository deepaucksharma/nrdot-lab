#
# OpenTelemetry configuration generator for ProcessSample Optimization Lab (PowerShell version)
# Creates OTel configurations from template with different intervals
#

Write-Host "Generating OpenTelemetry configuration files from template..." -ForegroundColor Cyan

# Directory setup
$ConfigDir = ".\config"
$TemplateFile = "$ConfigDir\otel-template.yaml"

# Check if template exists
if (-not (Test-Path $TemplateFile)) {
    Write-Host "Error: Template file $TemplateFile not found!" -ForegroundColor Red
    exit 1
}

# Function to generate OTel config with specific interval
function Generate-OtelConfig {
    param (
        [int]$Interval,
        [bool]$DockerStats = $false
    )
    
    $OutputFile = "$ConfigDir\otel-$($Interval)s.yaml"
    
    Write-Host "Generating $OutputFile with interval ${Interval}s..." -ForegroundColor Yellow
    
    # Read template content
    $TemplateContent = Get-Content $TemplateFile -Raw
    
    # Set interval replacement
    $TemplateContent = $TemplateContent -replace "\`${INTERVAL:-10s}", "${Interval}s"
    
    # Handle Docker stats
    if ($DockerStats) {
        $TemplateContent = $TemplateContent -replace "\`${ENABLE_DOCKER_STATS:\+docker}", "docker"
        $TemplateContent = $TemplateContent -replace "\`${ENABLE_DOCKER_STATS:\+collection_interval: \`${INTERVAL:-10s}}", "collection_interval: ${Interval}s"
        $TemplateContent = $TemplateContent -replace "\`${ENABLE_DOCKER_STATS:\+endpoint: unix:///var/run/docker.sock}", "endpoint: unix:///var/run/docker.sock"
        $TemplateContent = $TemplateContent -replace "\`${ENABLE_DOCKER_STATS:\+timeout: 20s}", "timeout: 20s"
        $TemplateContent = $TemplateContent -replace "\`${ENABLE_DOCKER_STATS:\+api_version: 1.24}", "api_version: 1.24"
        $TemplateContent = $TemplateContent -replace "\`${ENABLE_DOCKER_STATS:\+, docker}", ", docker"
    }
    else {
        $TemplateContent = $TemplateContent -replace "\`${ENABLE_DOCKER_STATS:\+docker}", ""
        $TemplateContent = $TemplateContent -replace "\`${ENABLE_DOCKER_STATS:\+collection_interval: \`${INTERVAL:-10s}}", ""
        $TemplateContent = $TemplateContent -replace "\`${ENABLE_DOCKER_STATS:\+endpoint: unix:///var/run/docker.sock}", ""
        $TemplateContent = $TemplateContent -replace "\`${ENABLE_DOCKER_STATS:\+timeout: 20s}", ""
        $TemplateContent = $TemplateContent -replace "\`${ENABLE_DOCKER_STATS:\+api_version: 1.24}", ""
        $TemplateContent = $TemplateContent -replace "\`${ENABLE_DOCKER_STATS:\+, docker}", ""
    }
    
    # Normalize hostname
    $TemplateContent = $TemplateContent -replace "\`${HOSTNAME}", "otel-collector"
    
    # Write to output file
    Set-Content -Path $OutputFile -Value $TemplateContent
    
    Write-Host "Generated $OutputFile" -ForegroundColor Green
}

# Generate main config file (default 10s interval)
Copy-Item -Path $TemplateFile -Destination "$ConfigDir\otel-config.yaml" -Force
Write-Host "Generated default config as otel-config.yaml" -ForegroundColor Green

# Generate configurations with different intervals
Generate-OtelConfig -Interval 5
Generate-OtelConfig -Interval 10
Generate-OtelConfig -Interval 20
Generate-OtelConfig -Interval 30

# Generate docker stats config
Generate-OtelConfig -Interval 10 -DockerStats $true
Move-Item -Path "$ConfigDir\otel-10s.yaml" -Destination "$ConfigDir\otel-docker.yaml" -Force

# Generate a lightweight config with fewer scrapers
$LiteConfig = "$ConfigDir\otel-scr-lite.yaml"
Write-Host "Generating lightweight config $LiteConfig..." -ForegroundColor Yellow

$TemplateContent = Get-Content $TemplateFile -Raw
$LiteContent = $TemplateContent -replace "disk:.*?[^\s]", ""
$LiteContent = $LiteContent -replace "filesystem:.*?[^\s]", ""
$LiteContent = $LiteContent -replace "paging:.*?[^\s]", ""
$LiteContent = $LiteContent -replace "network:.*?[^\s]", ""
$LiteContent = $LiteContent -replace "process:.*?enabled: true", ""

# Clean up any double blank lines
$LiteContent = $LiteContent -replace "`n`n`n", "`n`n"

Set-Content -Path $LiteConfig -Value $LiteContent
Write-Host "Generated $LiteConfig" -ForegroundColor Green

Write-Host "OpenTelemetry configuration generation complete." -ForegroundColor Cyan
