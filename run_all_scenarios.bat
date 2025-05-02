@echo off
:: Run all test scenarios for ProcessSample Optimization Lab
:: This is a streamlined version of the scenario testing script

echo ProcessSample Optimization Lab - Running all test scenarios
echo ------------------------------------------------------
echo.

:: Check for required environment variables
if "%NEW_RELIC_LICENSE_KEY%"=="" (
    if exist .env (
        echo Loading environment variables from .env file...
        for /F "tokens=*" %%A in (.env) do set %%A
    ) else (
        echo ERROR: NEW_RELIC_LICENSE_KEY environment variable is not set!
        echo Please set this variable or create a .env file.
        exit /b 1
    )
)

if "%NEW_RELIC_API_KEY%"=="" (
    echo WARNING: NEW_RELIC_API_KEY is not set. Validation will not work.
)

if "%NR_ACCOUNT_ID%"=="" (
    echo WARNING: NR_ACCOUNT_ID is not set. Validation will not work.
)

:: Create results directory
set TIMESTAMP=%date:~10,4%%date:~4,2%%date:~7,2%_%time:~0,2%%time:~3,2%%time:~6,2%
set TIMESTAMP=%TIMESTAMP: =%
set RESULTS_DIR=results\%TIMESTAMP%
mkdir %RESULTS_DIR% 2>nul

echo Saving results to %RESULTS_DIR%
echo.

:: Test duration (minutes)
set TEST_DURATION=10

:: Function to run a single test scenario
:run_scenario
    set SCEN=%~1
    set FILTER_TYPE=%~2
    set SAMPLE_RATE=%~3
    set EXTRA_OPTS=%~4
    
    echo Running scenario %SCEN%: Sample Rate=%SAMPLE_RATE%s, Filter=%FILTER_TYPE% %EXTRA_OPTS%
    
    :: Set environment variables
    set SAMPLE_RATE=%SAMPLE_RATE%
    set FILTER_TYPE=%FILTER_TYPE%
    
    :: Start the services with the specified configuration
    docker compose down -v >nul 2>&1
    docker compose up -d
    
    :: Wait for the specified duration
    echo Running test for %TEST_DURATION% minutes...
    powershell -Command "Start-Sleep -Seconds (%TEST_DURATION% * 60)"
    
    :: Capture Docker stats for resource usage
    docker stats --no-stream > %RESULTS_DIR%\%SCEN%_docker_stats.txt
    
    :: Run validation and save the results
    echo Validating and saving results...
    powershell -File scripts\validate.ps1 -Format json > %RESULTS_DIR%\%SCEN%.json
    
    :: Stop the services
    docker compose down -v >nul 2>&1
    
    echo Completed scenario %SCEN%
    echo.
    
    goto :eof

echo ---- Running baseline scenarios ----
call :run_scenario A-0 none 20
call :run_scenario A-1 standard 20
call :run_scenario A-2 standard 60

echo ---- Running sample rate sweep ----
call :run_scenario R-20 standard 20
call :run_scenario R-30 standard 30
call :run_scenario R-60 standard 60
call :run_scenario R-90 standard 90
call :run_scenario R-120 standard 120

echo ---- Running filter matrix ----
call :run_scenario F-none none 60
call :run_scenario F-standard standard 60
call :run_scenario F-aggressive aggressive 60
call :run_scenario F-targeted targeted 60

echo ---- Running OpenTelemetry study ----
set OTEL_INTERVAL=5s
call :run_scenario M-5 standard 60
set OTEL_INTERVAL=10s
call :run_scenario M-10 standard 60
set OTEL_INTERVAL=20s
call :run_scenario M-20 standard 60
set OTEL_INTERVAL=10s
set ENABLE_DOCKER_STATS=true
call :run_scenario M-docker standard 60
set ENABLE_DOCKER_STATS=

echo ---- Running command line options test ----
set COLLECT_CMDLINE=false
call :run_scenario C-off standard 60
set COLLECT_CMDLINE=true
call :run_scenario C-on standard 60
set COLLECT_CMDLINE=false

echo ---- Running load tests ----
set STRESS_CPU=1
set STRESS_MEM=64M
call :run_scenario L-light standard 60
set STRESS_CPU=8
set STRESS_MEM=1G
call :run_scenario L-heavy standard 60
set STRESS_CPU=2
set STRESS_MEM=128M
set STRESS_IO=2
call :run_scenario L-io standard 60
set STRESS_IO=0

echo All scenarios completed!
echo.
echo Generating visualizations...

python scripts\visualize.py --results-dir results --run %RESULTS_DIR%

echo.
echo Testing complete! View results in the %RESULTS_DIR% directory
echo and visualizations in the results\visualizations directory.
