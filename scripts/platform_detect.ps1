#
# Platform detection script for ProcessSample Optimization Lab (PowerShell version)
# Detects the platform and outputs appropriate commands and paths
#

# Platform detection
$Platform = $null
if ($PSVersionTable.Platform -eq "Unix") {
    if ($IsMacOS) {
        $Platform = "macos"
    } else {
        $Platform = "linux"
    }
} else {
    $Platform = "windows"
}

# Docker Compose command detection
$DockerComposeCmd = $null
try {
    $composeCheck = docker compose version 2>&1
    if ($LASTEXITCODE -eq 0) {
        $DockerComposeCmd = "docker compose"
    } else {
        throw "Docker compose command not found, trying docker-compose"
    }
} catch {
    try {
        $composeCheck = docker-compose --version 2>&1
        if ($LASTEXITCODE -eq 0) {
            $DockerComposeCmd = "docker-compose"
        } else {
            throw "Docker-compose command not found"
        }
    } catch {
        Write-Host "Error: Docker Compose not found. Please install Docker and Docker Compose." -ForegroundColor Red
        exit 1
    }
}

# Output platform info
Write-Host "PLATFORM=$Platform"
Write-Host "DOCKER_COMPOSE_CMD=$DockerComposeCmd"

# Output platform-specific paths
if ($Platform -eq "windows") {
    Write-Host "PATH_SEPARATOR=\"
    Write-Host "SCRIPT_EXT=.ps1"
} else {
    Write-Host "PATH_SEPARATOR=/"
    Write-Host "SCRIPT_EXT=.sh"
}

# Check for potential line ending issues
if ($Platform -eq "windows") {
    # Check for scripts that will run in Docker
    $dockerScripts = Get-ChildItem -Path "./load-image" -Filter "*.sh" -Recurse -ErrorAction SilentlyContinue
    
    $crlfDetected = $false
    foreach ($file in $dockerScripts) {
        $content = Get-Content -Path $file.FullName -Raw
        if ($content -match "\r\n") {
            $crlfDetected = $true
            break
        }
    }
    
    if ($crlfDetected) {
        Write-Host "WARNING: CRLF_DETECTED=true"
        Write-Host "Some shell scripts have Windows-style line endings (CRLF)."
        Write-Host "This may cause issues in Docker containers."
        Write-Host "Consider converting to Unix-style line endings (LF) using:"
        Write-Host "Get-ChildItem -Path './load-image' -Filter '*.sh' -Recurse | ForEach-Object { $content = Get-Content -Path $_.FullName -Raw; $content = $content -replace '\r\n', '\n'; Set-Content -Path $_.FullName -Value $content -NoNewline }"
    } else {
        Write-Host "CRLF_DETECTED=false"
    }
}

# Exit successfully
exit 0
