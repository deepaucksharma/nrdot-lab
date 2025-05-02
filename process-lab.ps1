#
# ProcessSample Optimization Lab - PowerShell Command Line Interface
# Cross-platform alternative to Makefile for Windows environments
#

param (
    [string]$Command = "help",
    [string]$Format = "text",
    [string]$FilterType = "standard",
    [int]$SampleRate = 60,
    [string]$ScenarioID = "",
    [switch]$DockerStats = $false,
    [switch]$MinimalMounts = $false,
    [switch]$SecureMode = $true
)

# Get script path for absolute references
$ScriptPath = Split-Path -Parent $MyInvocation.MyCommand.Definition

# Detect docker compose command
$DockerComposeCmd = "docker-compose"
try {
    $composeCheck = docker compose version 2>&1
    if ($LASTEXITCODE -eq 0) {
        $DockerComposeCmd = "docker compose"
    }
} catch {
    # Stick with docker-compose as the default
}

# Environment setup
$env:FILTER_TYPE = $FilterType
$env:SAMPLE_RATE = $SampleRate

if ($DockerStats) {
    $env:ENABLE_DOCKER_STATS = "true"
}
else {
    Remove-Item Env:\ENABLE_DOCKER_STATS -ErrorAction SilentlyContinue
}

if ($MinimalMounts) {
    $env:MIN_MOUNTS = ""
}
else {
    Remove-Item Env:\MIN_MOUNTS -ErrorAction SilentlyContinue
}

if ($SecureMode) {
    $env:SECURE_MODE = "true"
}
else {
    Remove-Item Env:\SECURE_MODE -ErrorAction SilentlyContinue
}

function Run-DockerCompose {
    param (
        [string]$Command,
        [string]$AdditionalArgs = ""
    )
    
    $fullCmd = "$DockerComposeCmd -f $ScriptPath\docker-compose.yml $Command $AdditionalArgs"
    Invoke-Expression $fullCmd
}

function Show-Help {
    Write-Host "`nProcessSample Optimization Lab - Command Line Interface`n" -ForegroundColor Cyan
    
    Write-Host "Core Commands:" -ForegroundColor Yellow
    Write-Host "  up                  Start the lab with standard configuration"
    Write-Host "  down                Stop the lab"
    Write-Host "  logs                View logs"
    Write-Host "  validate            Check ingestion stats (format: text, json, csv)"
    Write-Host "  clean               Remove all containers and volumes"
    Write-Host "  generate-configs    Generate all configurations from templates"
    
    Write-Host "`nConfiguration Options:" -ForegroundColor Yellow
    Write-Host "  filter-none         Use no process filtering"
    Write-Host "  filter-standard     Use standard process filtering"
    Write-Host "  filter-aggressive   Use aggressive process filtering"
    Write-Host "  filter-targeted     Use targeted process filtering"
    Write-Host "  sample-20           Use 20s sample rate (default NR)"
    Write-Host "  sample-60           Use 60s sample rate (recommended)"
    Write-Host "  sample-120          Use 120s sample rate (maximum savings)"
    Write-Host "  docker-stats        Enable Docker metrics collection"
    Write-Host "  minimal-mounts      Use minimal filesystem mounts"
    Write-Host "  secure-off          Disable seccomp security profiles"
    
    Write-Host "`nTesting Scenarios:" -ForegroundColor Yellow
    Write-Host "  baseline            Run baseline test (bare agent, no OTel)"
    Write-Host "  lab-baseline        Run lab baseline (default profiles)"
    Write-Host "  lab-opt             Run optimized lab config"
    Write-Host "  rate-sweep          Run tests with different sample rates"
    Write-Host "  filter-matrix       Run tests with different filtering configurations"
    Write-Host "  otel-study          Run tests analyzing OTel impact"
    Write-Host "  event-size          Run tests with different command line options"
    Write-Host "  load-light          Run with light load"
    Write-Host "  load-heavy          Run with heavy load"
    Write-Host "  load-io             Run with IO-focused load"
    
    Write-Host "`nVisualization:" -ForegroundColor Yellow
    Write-Host "  visualize           Generate result visualizations"
    
    Write-Host "`nUsage Examples:" -ForegroundColor Green
    Write-Host "  .\process-lab.ps1 up"
    Write-Host "  .\process-lab.ps1 validate -Format json"
    Write-Host "  .\process-lab.ps1 up -FilterType aggressive -SampleRate 120 -DockerStats"
    Write-Host "  .\process-lab.ps1 filter-aggressive"
    Write-Host ""
}

function Run-Scenario {
    param (
        [string]$Scenario,
        [hashtable]$ScenarioParams
    )
    
    $env:SCEN = $Scenario
    
    foreach ($key in $ScenarioParams.Keys) {
        Set-Item -Path "env:$key" -Value $ScenarioParams[$key]
    }
    
    & powershell -ExecutionPolicy Bypass -File "$ScriptPath\scripts\run_one.ps1"
}

# Command execution
switch -Regex ($Command) {
    "^up$" {
        Run-DockerCompose "up -d"
        Write-Host "Lab started with:" -ForegroundColor Green
        Write-Host "  - Filter type: $env:FILTER_TYPE"
        Write-Host "  - Sample rate: $env:SAMPLE_RATE seconds"
        Write-Host "  - Docker stats: $($DockerStats -eq $true)"
        Write-Host "  - Minimal mounts: $($MinimalMounts -eq $true)"
        Write-Host "  - Secure mode: $($SecureMode -eq $true)"
    }
    
    "^down$" {
        Run-DockerCompose "down"
        Write-Host "Lab stopped." -ForegroundColor Yellow
    }
    
    "^logs$" {
        Run-DockerCompose "logs -f"
    }
    
    "^validate$" {
        & powershell -ExecutionPolicy Bypass -File "$ScriptPath\scripts\validate_ingest.ps1" -Format $Format
    }
    
    "^clean$" {
        Run-DockerCompose "down -v"
        Write-Host "Lab stopped and volumes removed." -ForegroundColor Yellow
    }
    
    "^generate-configs$" {
        & powershell -ExecutionPolicy Bypass -File "$ScriptPath\scripts\generate_configs.ps1"
        & powershell -ExecutionPolicy Bypass -File "$ScriptPath\scripts\generate_otel_configs.ps1"
        Write-Host "Configurations generated from templates." -ForegroundColor Green
    }
    
    # Filter types
    "^filter-(none|standard|aggressive|targeted)$" {
        $filterType = $Command -replace "^filter-", ""
        $env:FILTER_TYPE = $filterType
        Run-DockerCompose "up -d"
        Write-Host "Lab started with $filterType filtering." -ForegroundColor Green
    }
    
    # Sample rates
    "^sample-(20|60|120)$" {
        $sampleRate = [int]($Command -replace "^sample-", "")
        $env:SAMPLE_RATE = $sampleRate
        Run-DockerCompose "up -d"
        Write-Host "Lab started with $sampleRate second sampling interval." -ForegroundColor Green
    }
    
    # Configuration variants
    "^docker-stats$" {
        $env:ENABLE_DOCKER_STATS = "true"
        Run-DockerCompose "up -d"
        Write-Host "Lab started with Docker stats collection enabled." -ForegroundColor Green
    }
    
    "^minimal-mounts$" {
        $env:MIN_MOUNTS = ""
        Run-DockerCompose "up -d"
        Write-Host "Lab started with minimal filesystem mounts." -ForegroundColor Green
    }
    
    "^secure-off$" {
        Remove-Item Env:\SECURE_MODE -ErrorAction SilentlyContinue
        Run-DockerCompose "up -d"
        Write-Host "Lab started with seccomp security profiles disabled." -ForegroundColor Green
    }
    
    # Testing scenarios
    "^baseline$" {
        Run-Scenario -Scenario "A-0" -ScenarioParams @{
            "PROFILE" = "bare-agent"
            "SAMPLE_RATE" = "20"
        }
    }
    
    "^lab-baseline$" {
        Run-Scenario -Scenario "A-1" -ScenarioParams @{
            "PROFILE" = "default"
            "SAMPLE_RATE" = "20"
        }
    }
    
    "^lab-opt$" {
        Run-Scenario -Scenario "A-2" -ScenarioParams @{
            "PROFILE" = "default"
            "SAMPLE_RATE" = "60"
            "FILTER_TYPE" = "standard"
        }
    }
    
    "^rate-sweep$" {
        @(20, 30, 60, 90, 120) | ForEach-Object {
            Run-Scenario -Scenario "R-$_" -ScenarioParams @{
                "PROFILE" = "default"
                "SAMPLE_RATE" = "$_"
            }
            Start-Sleep -Seconds 5
        }
    }
    
    "^filter-matrix$" {
        @("none", "standard", "aggressive", "targeted") | ForEach-Object {
            Run-Scenario -Scenario "F-$_" -ScenarioParams @{
                "PROFILE" = "default"
                "SAMPLE_RATE" = "60"
                "FILTER_TYPE" = "$_"
            }
            Start-Sleep -Seconds 5
        }
    }
    
    "^otel-study$" {
        # Base test without OTel
        Run-Scenario -Scenario "M-0" -ScenarioParams @{
            "PROFILE" = "bare-agent"
            "SAMPLE_RATE" = "60"
        }
        
        # Different OTel intervals
        @(5, 10, 20) | ForEach-Object {
            Run-Scenario -Scenario "M-$_" -ScenarioParams @{
                "PROFILE" = "default"
                "SAMPLE_RATE" = "60"
                "OTEL_INTERVAL" = "$_s"
            }
            Start-Sleep -Seconds 5
        }
        
        # With Docker stats
        Run-Scenario -Scenario "M-docker" -ScenarioParams @{
            "PROFILE" = "default"
            "SAMPLE_RATE" = "60"
            "ENABLE_DOCKER_STATS" = "true"
        }
    }
    
    "^event-size$" {
        # Without command line collection
        Run-Scenario -Scenario "C-off" -ScenarioParams @{
            "PROFILE" = "default"
            "SAMPLE_RATE" = "60"
            "COLLECT_CMDLINE" = "false"
        }
        
        # With command line collection
        Run-Scenario -Scenario "C-on" -ScenarioParams @{
            "PROFILE" = "default"
            "SAMPLE_RATE" = "60"
            "COLLECT_CMDLINE" = "true"
        }
    }
    
    "^load-(light|heavy|io)$" {
        $loadType = $Command -replace "^load-", ""
        
        switch ($loadType) {
            "light" {
                Run-Scenario -Scenario "L-light" -ScenarioParams @{
                    "PROFILE" = "default"
                    "SAMPLE_RATE" = "60"
                    "STRESS_CPU" = "1"
                    "STRESS_MEM" = "64M"
                }
            }
            "heavy" {
                Run-Scenario -Scenario "L-heavy" -ScenarioParams @{
                    "PROFILE" = "default"
                    "SAMPLE_RATE" = "60"
                    "STRESS_CPU" = "8"
                    "STRESS_MEM" = "1G"
                }
            }
            "io" {
                Run-Scenario -Scenario "L-io" -ScenarioParams @{
                    "PROFILE" = "default"
                    "SAMPLE_RATE" = "60"
                    "STRESS_IO" = "2"
                }
            }
        }
    }
    
    "^visualize$" {
        python "$ScriptPath\scripts\visualize.py"
        Write-Host "Visualizations generated." -ForegroundColor Green
    }
    
    "^help$" {
        Show-Help
    }
    
    default {
        Write-Host "Unknown command: $Command" -ForegroundColor Red
        Show-Help
    }
}