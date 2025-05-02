# Verification script for ProcessSample Optimization Lab
$ErrorActionPreference = "Stop"

Write-Host "========================================================" -ForegroundColor Cyan
Write-Host "ProcessSample Optimization Lab - Environment Verification" -ForegroundColor Cyan
Write-Host "========================================================" -ForegroundColor Cyan

# Check for required directories and files
$requiredDirs = @(
    ".\config",
    ".\scripts",
    ".\profiles",
    ".\results"
)

$requiredFiles = @(
    ".\scripts\validate_ingest.ps1",
    ".\scripts\generate_configs.ps1",
    ".\scripts\generate_otel_configs.ps1",
    ".\scripts\visualize.py",
    ".\config\newrelic-infra-template.yml",
    ".\config\filter-definitions.yml",
    ".\config\otel-template.yaml",
    ".\docker-compose.yml",
    ".\process-lab.ps1",
    ".\run_all_scenarios.bat"
)

$configFiles = @(
    ".\config\newrelic-infra-standard.yml",
    ".\config\newrelic-infra-aggressive.yml",
    ".\config\newrelic-infra-targeted.yml",
    ".\config\newrelic-infra-none.yml",
    ".\config\otel-config.yaml",
    ".\config\otel-5s.yaml",
    ".\config\otel-20s.yaml"
)

$anyErrors = $false

# Check directories
Write-Host "`nVerifying required directories..." -ForegroundColor Yellow
foreach ($dir in $requiredDirs) {
    if (Test-Path $dir) {
        Write-Host "✅ $dir"
    } else {
        Write-Host "❌ $dir not found" -ForegroundColor Red
        $anyErrors = $true
    }
}

# Check files
Write-Host "`nVerifying required files..." -ForegroundColor Yellow
foreach ($file in $requiredFiles) {
    if (Test-Path $file) {
        Write-Host "✅ $file"
    } else {
        Write-Host "❌ $file not found" -ForegroundColor Red
        $anyErrors = $true
    }
}

# Check if config files exist or need to be generated
$configsMissing = $false
Write-Host "`nChecking configuration files..." -ForegroundColor Yellow
foreach ($file in $configFiles) {
    if (Test-Path $file) {
        Write-Host "✅ $file"
    } else {
        Write-Host "ℹ️ $file will be generated" -ForegroundColor Yellow
        $configsMissing = $true
    }
}

if ($configsMissing) {
    Write-Host "`nSome configuration files are missing. Do you want to generate them now? (y/n)" -ForegroundColor Yellow
    $response = Read-Host
    if ($response -eq "y" -or $response -eq "Y") {
        Write-Host "Generating configuration files..." -ForegroundColor Green
        try {
            & powershell -ExecutionPolicy Bypass -File .\scripts\generate_configs.ps1
            & powershell -ExecutionPolicy Bypass -File .\scripts\generate_otel_configs.ps1
            Write-Host "Configuration generation complete." -ForegroundColor Green
        }
        catch {
            Write-Host "❌ Failed to generate configurations: $_" -ForegroundColor Red
            $anyErrors = $true
        }
    }
}

# Check Docker
Write-Host "`nVerifying Docker is running..." -ForegroundColor Yellow
try {
    $dockerStatus = docker info 2>&1
    if ($LASTEXITCODE -eq 0) {
        Write-Host "✅ Docker is running"
        
        # Check Docker Compose
        try {
            $composeCheck = docker-compose --version 2>&1
            if ($LASTEXITCODE -eq 0) {
                Write-Host "✅ Docker Compose is available"
            }
            else {
                Write-Host "❌ Docker Compose is not available" -ForegroundColor Red
                $anyErrors = $true
            }
        }
        catch {
            Write-Host "❌ Docker Compose check failed: $_" -ForegroundColor Red
            $anyErrors = $true
        }
    } else {
        Write-Host "❌ Docker is not running" -ForegroundColor Red
        $anyErrors = $true
    }
} 
catch {
    Write-Host "❌ Docker command failed: $_" -ForegroundColor Red
    $anyErrors = $true
}

# Check Python for visualization
Write-Host "`nVerifying Python installation for visualization..." -ForegroundColor Yellow
try {
    $pythonVersion = python --version 2>&1
    if ($LASTEXITCODE -eq 0) {
        Write-Host "✅ Python is installed: $pythonVersion"
        
        # Check matplotlib
        try {
            python -c "import matplotlib" 2>&1
            if ($LASTEXITCODE -eq 0) {
                Write-Host "✅ matplotlib is installed"
            }
            else {
                Write-Host "ℹ️ matplotlib is not installed - visualization will not work" -ForegroundColor Yellow
                Write-Host "   Install with: pip install matplotlib numpy"
            }
        }
        catch {
            Write-Host "ℹ️ matplotlib check failed - visualization will not work" -ForegroundColor Yellow
            Write-Host "   Install with: pip install matplotlib numpy"
        }
    } else {
        Write-Host "ℹ️ Python is not installed - visualization will not work" -ForegroundColor Yellow
        Write-Host "   Install Python 3.6+ to use visualization features"
    }
} 
catch {
    Write-Host "ℹ️ Python check failed - visualization will not work" -ForegroundColor Yellow
    Write-Host "   Install Python 3.6+ to use visualization features"
}

# Check environment variables or .env file
Write-Host "`nChecking for required environment variables..." -ForegroundColor Yellow
$envVars = @("NEW_RELIC_LICENSE_KEY", "NEW_RELIC_API_KEY", "NR_ACCOUNT_ID")
$missingVars = @()

# First check environment variables
foreach ($var in $envVars) {
    $value = [Environment]::GetEnvironmentVariable($var)
    if ([string]::IsNullOrEmpty($value)) {
        $missingVars += $var
    }
}

# If any variables are missing, check the .env file
if ($missingVars.Count -gt 0 -and (Test-Path .env)) {
    Write-Host "ℹ️ Some environment variables are missing, checking .env file..." -ForegroundColor Yellow
    $envContent = Get-Content .env -Raw
    
    foreach ($var in $missingVars.Clone()) {
        if ($envContent -match "$var=([^`r`n]*)") {
            Write-Host "✅ $var found in .env file"
            $missingVars = $missingVars | Where-Object { $_ -ne $var }
        }
    }
}

if ($missingVars.Count -eq 0) {
    Write-Host "✅ All required environment variables are set"
} else {
    Write-Host "❌ Missing environment variables: $($missingVars -join ', ')" -ForegroundColor Red
    Write-Host "   Please set these in your .env file or as environment variables."
    $anyErrors = $true
}

# Summary
Write-Host "`n========================================================" -ForegroundColor Cyan
if ($anyErrors) {
    Write-Host "❌ Verification FAILED. Please fix the issues above." -ForegroundColor Red
    Write-Host "   Run .\setup.ps1 to try automated setup." -ForegroundColor Yellow
} else {
    Write-Host "✅ Verification PASSED. Your environment is ready." -ForegroundColor Green
    Write-Host "`nQuick start commands:" -ForegroundColor Cyan
    Write-Host "   Start default lab:  .\process-lab.ps1 up"
    Write-Host "   Validate results:   .\process-lab.ps1 validate"
    Write-Host "   Try filter types:   .\process-lab.ps1 filter-aggressive"
    Write-Host "   Run all scenarios:  .\run_all_scenarios.bat" 
    Write-Host "   Show all options:   .\process-lab.ps1 help"
}
Write-Host "========================================================" -ForegroundColor Cyan