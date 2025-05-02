#
# Setup script for ProcessSample Optimization Lab (PowerShell version)
# Initializes the project with all required configurations
#

Write-Host "========================================================" -ForegroundColor Cyan
Write-Host "  ProcessSample Optimization Lab - Initial Setup" -ForegroundColor Cyan
Write-Host "========================================================" -ForegroundColor Cyan
Write-Host

# Check for Docker
try {
    $dockerVersion = docker --version
    Write-Host "Docker detected: $dockerVersion" -ForegroundColor Green
}
catch {
    Write-Host "Error: Docker is not installed or not in PATH." -ForegroundColor Red
    Write-Host "Please install Docker before continuing."
    exit 1
}

# Check Docker Compose
try {
    $composeVersion = docker compose version
    Write-Host "Docker Compose detected: $composeVersion" -ForegroundColor Green
}
catch {
    Write-Host "Error: Docker Compose is not installed or not in PATH." -ForegroundColor Red
    Write-Host "Please ensure you have Docker Desktop with Docker Compose v2 enabled."
    exit 1
}

# Check for environment file
if (-not (Test-Path .env)) {
    if (Test-Path .env.example) {
        Write-Host "Creating .env file from example..." -ForegroundColor Yellow
        Copy-Item .env.example .env
        Write-Host "Please edit .env with your New Relic license key, API key, and account ID."
    }
    else {
        Write-Host "Error: .env.example file not found." -ForegroundColor Red
        exit 1
    }
}

# Check for Python (needed for visualization)
try {
    $pythonVersion = python --version
    Write-Host "Python detected: $pythonVersion" -ForegroundColor Green
}
catch {
    try {
        $pythonVersion = python3 --version
        Write-Host "Python detected: $pythonVersion" -ForegroundColor Green
    }
    catch {
        Write-Host "Warning: Python not detected. Visualization features will not work." -ForegroundColor Yellow
        Write-Host "Please install Python 3.6+ if you want to use visualization features."
    }
}

# Generate configurations
Write-Host "Generating configurations..." -ForegroundColor Yellow
& powershell -ExecutionPolicy Bypass -File .\scripts\generate_configs.ps1
& powershell -ExecutionPolicy Bypass -File .\scripts\generate_otel_configs.ps1

# Create necessary directories
Write-Host "Creating directory structure..." -ForegroundColor Yellow
New-Item -ItemType Directory -Path results -Force | Out-Null
New-Item -ItemType Directory -Path results\visualizations -Force | Out-Null

# Verify setup
Write-Host "Verifying setup..." -ForegroundColor Yellow
if (-not (Test-Path "config\newrelic-infra-standard.yml")) {
    Write-Host "Error: Configuration generation failed." -ForegroundColor Red
    exit 1
}

if (-not (Test-Path "config\otel-config.yaml")) {
    Write-Host "Error: OpenTelemetry configuration generation failed." -ForegroundColor Red
    exit 1
}

Write-Host
Write-Host "Setup completed successfully!" -ForegroundColor Green
Write-Host

Write-Host "Next steps:" -ForegroundColor Cyan
Write-Host "  1. Edit .env with your New Relic license key, API key, and account ID"
Write-Host "  2. Run '.\process-lab.ps1 up' to start the lab"
Write-Host "  3. Wait 5-10 minutes for data collection"
Write-Host "  4. Run '.\process-lab.ps1 validate' to check the results"
Write-Host
Write-Host "For more options, run '.\process-lab.ps1 help'"
Write-Host
