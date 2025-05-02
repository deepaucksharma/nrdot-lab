#
# Prepare Script for ProcessSample Optimization Lab
# Sets up the environment and prepares for pushing changes
#

Write-Host "Preparing ProcessSample Optimization Lab for pushing..." -ForegroundColor Cyan
Write-Host "=======================================================" -ForegroundColor Cyan
Write-Host

# Get script directory
$ScriptPath = Split-Path -Parent $MyInvocation.MyCommand.Definition

# Step 1: Run platform detection
Write-Host "Step 1: Detecting platform and environment..." -ForegroundColor Yellow
& powershell -ExecutionPolicy Bypass -File "$ScriptPath\scripts\platform_detect.ps1"
Write-Host "Platform detection complete." -ForegroundColor Green
Write-Host

# Step 2: Fix line endings
Write-Host "Step 2: Fixing line endings in shell scripts..." -ForegroundColor Yellow
& powershell -ExecutionPolicy Bypass -File "$ScriptPath\scripts\fix_line_endings.ps1"
Write-Host

# Step 3: Generate configurations
Write-Host "Step 3: Generating configurations..." -ForegroundColor Yellow
& powershell -ExecutionPolicy Bypass -File "$ScriptPath\scripts\generate_configs.ps1"
& powershell -ExecutionPolicy Bypass -File "$ScriptPath\scripts\generate_otel_configs.ps1"
Write-Host "Configuration generation complete." -ForegroundColor Green
Write-Host

# Step 4: Verify setup
Write-Host "Step 4: Verifying setup..." -ForegroundColor Yellow
& powershell -ExecutionPolicy Bypass -File "$ScriptPath\verify_setup.ps1"
Write-Host

# Step 5: Instructions for pushing
Write-Host "Step 5: Preparation for pushing to repository..." -ForegroundColor Yellow
Write-Host "To push changes to your repository, run the following Git commands:" -ForegroundColor Cyan
Write-Host
Write-Host "git add ." -ForegroundColor White
Write-Host "git commit -m 'Streamline ProcessSample Lab project end-to-end'" -ForegroundColor White
Write-Host "git push origin main" -ForegroundColor White
Write-Host
Write-Host "If using a branch:" -ForegroundColor Cyan
Write-Host "git checkout -b streamlined-version" -ForegroundColor White
Write-Host "git add ." -ForegroundColor White
Write-Host "git commit -m 'Streamline ProcessSample Lab project end-to-end'" -ForegroundColor White
Write-Host "git push origin streamlined-version" -ForegroundColor White
Write-Host

Write-Host "Preparation complete!" -ForegroundColor Green
