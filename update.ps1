#
# Update script for ProcessSample Optimization Lab (PowerShell version)
# Updates an existing installation to the latest streamlined structure
#

Write-Host "========================================================" -ForegroundColor Cyan
Write-Host "  ProcessSample Optimization Lab - Update" -ForegroundColor Cyan
Write-Host "========================================================" -ForegroundColor Cyan
Write-Host

# Check if this is a valid installation
if (-not (Test-Path "config") -or -not (Test-Path "docker-compose.yml")) {
    Write-Host "Error: This doesn't appear to be a valid ProcessSample Lab directory." -ForegroundColor Red
    Write-Host "Please run this script from the root of the ProcessSample Lab project."
    exit 1
}

# Create backup of important files
Write-Host "Creating backup of current configuration..." -ForegroundColor Yellow
$BackupDir = "backup_$(Get-Date -Format 'yyyyMMdd_HHmmss')"
New-Item -ItemType Directory -Path $BackupDir -Force | Out-Null

# Backup important user files
if (Test-Path ".env") {
    Copy-Item -Path ".env" -Destination $BackupDir
}

if (Test-Path "docker-compose.override.yml") {
    Copy-Item -Path "docker-compose.override.yml" -Destination $BackupDir
}

if (Test-Path "config\newrelic-infra.yml") {
    Copy-Item -Path "config\newrelic-infra.yml" -Destination $BackupDir
}

if (Test-Path "config\otel-config.yaml") {
    Copy-Item -Path "config\otel-config.yaml" -Destination $BackupDir
}

Write-Host "Backup created in $BackupDir" -ForegroundColor Green

# Ensure the lab is stopped
Write-Host "Stopping any running containers..." -ForegroundColor Yellow
try {
    docker compose down 2>$null
} catch {
    # Ignore errors if docker compose fails
}

# Generate new configurations
Write-Host "Generating updated configurations..." -ForegroundColor Yellow
& powershell -ExecutionPolicy Bypass -File .\scripts\generate_configs.ps1
& powershell -ExecutionPolicy Bypass -File .\scripts\generate_otel_configs.ps1

# Verify update
Write-Host "Verifying update..." -ForegroundColor Yellow
if (-not (Test-Path "config\newrelic-infra-standard.yml") -or -not (Test-Path "config\otel-config.yaml")) {
    Write-Host "Error: Configuration generation failed." -ForegroundColor Red
    Write-Host "The update was not successful."
    exit 1
}

Write-Host
Write-Host "Update completed successfully!" -ForegroundColor Green
Write-Host
Write-Host "Changes:" -ForegroundColor Cyan
Write-Host "  - Configuration system is now template-based"
Write-Host "  - Docker Compose has been unified into a single file"
Write-Host "  - Scripts have been streamlined and improved"
Write-Host "  - Cross-platform support has been added"
Write-Host
Write-Host "Your previous configuration has been backed up to $BackupDir" -ForegroundColor Yellow
Write-Host
Write-Host "Next steps:" -ForegroundColor Cyan
Write-Host "  1. Run '.\process-lab.ps1 up' to start the lab with the updated configuration"
Write-Host "  2. Wait 5-10 minutes for data collection"
Write-Host "  3. Run '.\process-lab.ps1 validate' to check the results"
Write-Host
Write-Host "For more options, run '.\process-lab.ps1 help'"
Write-Host
