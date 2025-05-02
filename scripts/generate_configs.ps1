#
# Configuration generator for ProcessSample Optimization Lab (PowerShell version)
# Creates NewRelic Infrastructure configurations from templates
#

Write-Host "Generating New Relic Infrastructure configuration files from templates..." -ForegroundColor Cyan

# Directory setup
$ConfigDir = ".\config"
$TemplateFile = "$ConfigDir\newrelic-infra-template.yml"
$FilterDefinitions = "$ConfigDir\filter-definitions.yml"

# Check if template exists
if (-not (Test-Path $TemplateFile)) {
    Write-Host "Error: Template file $TemplateFile not found!" -ForegroundColor Red
    exit 1
}

# Check if filter definitions exist
if (-not (Test-Path $FilterDefinitions)) {
    Write-Host "Error: Filter definitions file $FilterDefinitions not found!" -ForegroundColor Red
    exit 1
}

# Function to generate configurations for each filter type
function Generate-Config {
    param (
        [string]$FilterType,
        [int]$SampleRate = 60,
        [bool]$CollectCmdline = $false
    )
    
    $OutputFile = "$ConfigDir\newrelic-infra-$FilterType.yml"
    
    Write-Host "Generating $OutputFile with sample rate $SampleRate..." -ForegroundColor Yellow
    
    # Start with template content
    $TemplateContent = Get-Content $TemplateFile -Raw
    
    # Set sample rate
    $TemplateContent = $TemplateContent -replace "metrics_process_sample_rate:.*", "metrics_process_sample_rate: $SampleRate"
    
    # Set command line collection
    if ($CollectCmdline) {
        $TemplateContent = $TemplateContent -replace "collect_command_line:.*", "collect_command_line: true"
    }
    else {
        $TemplateContent = $TemplateContent -replace "collect_command_line:.*", "collect_command_line: false"
    }
    
    # Apply filter definitions
    $FilterContent = Get-Content $FilterDefinitions -Raw
    
    switch ($FilterType) {
        "none" {
            # Remove all process filtering
            $TemplateContent = $TemplateContent -replace "exclude_matching_metrics:(\s+.*\n)+", "exclude_matching_metrics: {}`n"
        }
        
        "standard" {
            # Extract standard filter section from definitions
            if ($FilterContent -match '# STANDARD FILTER START(.*?)# STANDARD FILTER END') {
                $StandardFilter = $Matches[1]
                # Remove comment lines
                $StandardFilter = $StandardFilter -replace '#.*\n', ''
                # Add the filter section to the template
                $TemplateContent = $TemplateContent -replace "exclude_matching_metrics:.*", "exclude_matching_metrics:$StandardFilter"
            }
        }
        
        "aggressive" {
            # Extract aggressive filter section from definitions
            if ($FilterContent -match '# AGGRESSIVE FILTER START(.*?)# AGGRESSIVE FILTER END') {
                $AggressiveFilter = $Matches[1]
                # Remove comment lines
                $AggressiveFilter = $AggressiveFilter -replace '#.*\n', ''
                # Add the filter section to the template
                $TemplateContent = $TemplateContent -replace "exclude_matching_metrics:.*", "exclude_matching_metrics:$AggressiveFilter"
            }
        }
        
        "targeted" {
            # Extract targeted filter section from definitions
            if ($FilterContent -match '# TARGETED FILTER START(.*?)# TARGETED FILTER END') {
                $TargetedFilter = $Matches[1]
                # Remove comment lines
                $TargetedFilter = $TargetedFilter -replace '#.*\n', ''
                # Add the filter section to the template
                $TemplateContent = $TemplateContent -replace "exclude_matching_metrics:.*", "exclude_matching_metrics:$TargetedFilter"
            }
        }
        
        default {
            Write-Host "Unknown filter type: $FilterType" -ForegroundColor Red
            exit 1
        }
    }
    
    # Write the final content to the output file
    Set-Content -Path $OutputFile -Value $TemplateContent
    
    Write-Host "Generated $OutputFile" -ForegroundColor Green
}

# Generate configurations for all filter types
Generate-Config -FilterType "none" -SampleRate 60 -CollectCmdline $false
Generate-Config -FilterType "standard" -SampleRate 60 -CollectCmdline $false
Generate-Config -FilterType "aggressive" -SampleRate 60 -CollectCmdline $false
Generate-Config -FilterType "targeted" -SampleRate 60 -CollectCmdline $false

Write-Host "Configuration generation complete." -ForegroundColor Cyan
