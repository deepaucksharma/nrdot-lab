# Verification script for ProcessSample testing setup
$ErrorActionPreference = "Stop"

Write-Host "========================================"
Write-Host "ProcessSample Test Environment Verification"
Write-Host "========================================"

# Check for required directories and files
$requiredDirs = @(
    ".\config",
    ".\overrides",
    ".\overrides\filters",
    ".\scripts",
    ".\profiles",
    ".\results"
)

$requiredFiles = @(
    ".\scripts\run_one.ps1",
    ".\scripts\validate_ingest.ps1",
    ".\scripts\vis_latency_win.py",
    ".\scripts\healthcheck.ps1",
    ".\scripts\generate_visualization.py",
    ".\config\newrelic-infra.yml",
    ".\config\otel-config.yaml",
    ".\profiles\bare-agent.yml",
    ".\overrides\filters\none.yml",
    ".\run_all_scenarios.bat"
)

$anyErrors = $false

# Check directories
Write-Host "`nVerifying required directories..."
foreach ($dir in $requiredDirs) {
    if (Test-Path $dir) {
        Write-Host "✅ $dir"
    } else {
        Write-Host "❌ $dir not found"
        $anyErrors = $true
    }
}

# Check files
Write-Host "`nVerifying required files..."
foreach ($file in $requiredFiles) {
    if (Test-Path $file) {
        Write-Host "✅ $file"
    } else {
        Write-Host "❌ $file not found"
        $anyErrors = $true
    }
}

# Check Docker
Write-Host "`nVerifying Docker is running..."
try {
    $dockerStatus = docker info 2>&1
    if ($LASTEXITCODE -eq 0) {
        Write-Host "✅ Docker is running"
    } else {
        Write-Host "❌ Docker is not running"
        $anyErrors = $true
    }
} catch {
    Write-Host "❌ Docker command failed: $_"
    $anyErrors = $true
}

# Check environment variables
Write-Host "`nChecking for required environment variables..."
$envVars = @("NEW_RELIC_LICENSE_KEY", "NEW_RELIC_API_KEY", "NR_ACCOUNT_ID")
$missingVars = @()

foreach ($var in $envVars) {
    $value = [Environment]::GetEnvironmentVariable($var)
    if ([string]::IsNullOrEmpty($value)) {
        $missingVars += $var
    }
}

if ($missingVars.Count -eq 0) {
    Write-Host "✅ All required environment variables are set"
} else {
    Write-Host "❌ Missing environment variables: $($missingVars -join ', ')"
    Write-Host "   Please set these in .env file or run_all_scenarios.bat"
    $anyErrors = $true
}

# Summary
Write-Host "`n========================================"
if ($anyErrors) {
    Write-Host "❌ Verification FAILED. Please fix the issues above."
    Write-Host "   See SCENARIO_TESTING.md for setup instructions."
} else {
    Write-Host "✅ Verification PASSED. Your environment is ready."
    Write-Host "   You can now run: powershell -Command `".\scripts\run_one.ps1 -SCEN 'A-0' -PROFILE 'bare-agent' -SAMPLE 20 -DURATION 5`""
}
Write-Host "========================================"
