# PowerShell healthcheck for infrastructure agent and OTel collector

Write-Host "Checking New Relic Infrastructure Agent..."
$infraRunning = docker ps | Select-String -Pattern "nr-infra"

if ($infraRunning) {
    $infraHealth = docker exec nr-infra curl -s http://localhost:18003/status 2>$null
    if ($infraHealth -and $infraHealth -match "agent status") {
        Write-Host "✅ Infrastructure agent is healthy"
        $infraOk = $true
    } else {
        Write-Host "❌ Infrastructure agent is not responding"
        $infraOk = $false
    }
} else {
    Write-Host "❌ Infrastructure agent is not running"
    $infraOk = $false
}

# Check OTel collector if it's running
$otelRunning = docker ps | Select-String -Pattern "otel-collector"
if ($otelRunning) {
    Write-Host "Checking OpenTelemetry Collector..."
    $otelHealth = docker exec otel-collector wget -qO- http://localhost:13133/healthz 2>$null
    if ($otelHealth -and $otelHealth -match "healthcheck status") {
        Write-Host "✅ OpenTelemetry collector is healthy"
        $otelOk = $true
    } else {
        Write-Host "❌ OpenTelemetry collector is not responding"
        $otelOk = $false
    }
} else {
    Write-Host "ℹ️ OpenTelemetry collector is not running"
    $otelOk = $true  # Not running is OK if it's not part of the scenario
}

# Return combined status
if ($infraOk -and $otelOk) {
    Write-Host "🟢 All components healthy"
    exit 0
} else {
    Write-Host "🔴 One or more components unhealthy"
    exit 1
}
