# Configuration file generator script for Windows
# Usage: .\generate_config.ps1 -FilterType <filter_type> -SampleRate <rate> -CollectCmdline <bool>
# Example: .\generate_config.ps1 -FilterType aggressive -SampleRate 60 -CollectCmdline $false

param (
    [Parameter(Position=0)]
    [ValidateSet("standard", "aggressive", "targeted", "none")]
    [string]$FilterType = "standard",
    
    [Parameter(Position=1)]
    [int]$SampleRate = 60,
    
    [Parameter(Position=2)]
    [bool]$CollectCmdline = $false
)

# Set file paths
$templateFile = Join-Path $PSScriptRoot "..\config\newrelic-infra-template.yml"
$filterDefsFile = Join-Path $PSScriptRoot "..\config\filter-definitions.yml"
$outputDir = Join-Path $PSScriptRoot "..\config"
$outputFile = Join-Path $outputDir "newrelic-infra-$FilterType.yml"

# Check if template file exists
if (-not (Test-Path $templateFile)) {
    Write-Error "Template file not found: $templateFile"
    exit 1
}

# Check if filter definitions file exists
if (-not (Test-Path $filterDefsFile)) {
    Write-Error "Filter definitions file not found: $filterDefsFile"
    exit 1
}

# Read template content
$templateContent = Get-Content -Path $templateFile -Raw

# Read filter definition content
$filterDefsContent = Get-Content -Path $filterDefsFile -Raw

# Extract filter configuration based on filter type
if ($FilterType -eq "none") {
    $filterConfig = "# No process filtering"
}
else {
    # Find the section for the filter type
    $pattern = "(?ms)^$FilterType:\s*\r?\n((?:  .*\r?\n)+)"
    if ($filterDefsContent -match $pattern) {
        $filterConfig = $matches[1]
    }
    else {
        Write-Error "Could not find filter type $FilterType in filter definitions file"
        exit 1
    }
}

# Replace variables in template
$outputContent = $templateContent -replace '\${SAMPLE_RATE:-60}', $SampleRate
$outputContent = $outputContent -replace '\${COLLECT_CMDLINE:-false}', $CollectCmdline.ToString().ToLower()
$outputContent = $outputContent -replace '\${FILTER_CONFIG}', $filterConfig

# Write to output file
Set-Content -Path $outputFile -Value $outputContent

Write-Host "Generated $outputFile with $FilterType filters, sample rate: $SampleRate, collect_cmdline: $($CollectCmdline.ToString().ToLower())"
