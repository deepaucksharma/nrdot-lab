@echo off
REM Process Optimization Lab Command Wrapper for Windows
REM This batch file makes it easier to run common commands

IF "%1"=="" (
    GOTO help
)

IF "%1"=="up" (
    docker-compose -f docker-compose.unified.yml up -d
    GOTO end
)

IF "%1"=="down" (
    docker-compose -f docker-compose.unified.yml down
    GOTO end
)

IF "%1"=="generate-configs" (
    powershell -File .\scripts\generate_config.ps1 -FilterType standard -SampleRate 60 -CollectCmdline $false
    powershell -File .\scripts\generate_config.ps1 -FilterType aggressive -SampleRate 60 -CollectCmdline $false
    powershell -File .\scripts\generate_config.ps1 -FilterType targeted -SampleRate 60 -CollectCmdline $false
    powershell -File .\scripts\generate_config.ps1 -FilterType none -SampleRate 60 -CollectCmdline $false
    GOTO end
)

IF "%1"=="validate" (
    powershell -File .\scripts\validate.ps1
    GOTO end
)

IF "%1"=="filter-aggressive" (
    SET FILTER_TYPE=aggressive
    docker-compose -f docker-compose.unified.yml up -d
    GOTO end
)

IF "%1"=="filter-standard" (
    SET FILTER_TYPE=standard
    docker-compose -f docker-compose.unified.yml up -d
    GOTO end
)

IF "%1"=="filter-targeted" (
    SET FILTER_TYPE=targeted
    docker-compose -f docker-compose.unified.yml up -d
    GOTO end
)

IF "%1"=="filter-none" (
    SET FILTER_TYPE=none
    docker-compose -f docker-compose.unified.yml up -d
    GOTO end
)

IF "%1"=="visualize" (
    python .\scripts\visualize.py --input .\results\latest.json --output .\results\visualization
    GOTO end
)

IF "%1"=="logs" (
    docker-compose -f docker-compose.unified.yml logs -f
    GOTO end
)

IF "%1"=="help" (
    GOTO help
)

echo Unknown command: %1
GOTO help

:help
echo.
echo Process Optimization Lab Command Wrapper
echo ======================================
echo.
echo Available commands:
echo   up                   Start the lab with default settings
echo   down                 Stop the lab
echo   generate-configs     Generate all configuration files
echo   validate             Validate ProcessSample data in New Relic
echo   filter-aggressive    Start with aggressive filtering
echo   filter-standard      Start with standard filtering
echo   filter-targeted      Start with targeted filtering
echo   filter-none          Start with no filtering
echo   visualize            Generate visualizations from results
echo   logs                 View container logs
echo   help                 Show this help message
echo.

:end
