@echo off
echo ========================================
echo Running All ProcessSample Optimization Scenarios
echo ========================================

REM Set required environment variables - replace with your values
set NEW_RELIC_LICENSE_KEY=your_license_key_here
set NEW_RELIC_API_KEY=your_api_key_here  
set NR_ACCOUNT_ID=your_account_id_here

REM Create results directory
if not exist results mkdir results

echo.
echo === Running simple healthcheck ===
powershell -Command ".\scripts\healthcheck.ps1"
if %ERRORLEVEL% NEQ 0 (
    echo Failed healthcheck, aborting tests
    exit /b 1
)

echo.
echo === Category 1: Baseline & Core-Opt ===
powershell -Command ".\scripts\run_one.ps1 -SCEN 'A-0' -PROFILE 'bare-agent' -SAMPLE 20 -DURATION 10"
powershell -Command ".\scripts\run_one.ps1 -SCEN 'A-1' -PROFILE 'default' -SAMPLE 20 -DURATION 10"
powershell -Command ".\scripts\run_one.ps1 -SCEN 'A-2' -PROFILE 'default' -SAMPLE 60 -FILTER 'yes' -DURATION 10"

echo.
echo === Category 2: Sample-Rate Sweep (shortened version) ===
powershell -Command ".\scripts\run_one.ps1 -SCEN 'R-20' -SAMPLE 20 -DURATION 10"
powershell -Command ".\scripts\run_one.ps1 -SCEN 'R-60' -SAMPLE 60 -DURATION 10"
powershell -Command ".\scripts\run_one.ps1 -SCEN 'R-120' -SAMPLE 120 -DURATION 10"

echo.
echo === Category 3: Filtering Matrix (shortened version) ===
powershell -Command ".\scripts\run_one.ps1 -SCEN 'F-none' -FILTER 'no' -DURATION 10"
powershell -Command ".\scripts\run_one.ps1 -SCEN 'F-current' -DURATION 10"

echo.
echo === Category 4: OTel Contribution Study (shortened version) ===
powershell -Command ".\scripts\run_one.ps1 -SCEN 'M-0' -PROFILE 'bare-agent' -DURATION 10"
powershell -Command ".\scripts\run_one.ps1 -SCEN 'M-10' -DURATION 10"

echo.
echo === Category 5: Event Size Impact ===
powershell -Command ".\scripts\run_one.ps1 -SCEN 'C-off' -DURATION 10"
powershell -Command ".\scripts\run_one.ps1 -SCEN 'C-on' -COLLECT_CMDLINE 'true' -DURATION 10"
powershell -Command ".\scripts\run_one.ps1 -SCEN 'C-strip' -COLLECT_CMDLINE 'true' -STRIP_CMDLINE 'true' -DURATION 10"

echo.
echo === Category 6: Load Robustness ===
powershell -Command ".\scripts\run_one.ps1 -SCEN 'L-light' -STRESS_CPU 1 -STRESS_MEM '64M' -DURATION 10"
powershell -Command ".\scripts\run_one.ps1 -SCEN 'L-heavy' -STRESS_CPU 8 -STRESS_MEM '1G' -DURATION 10"

echo.
echo === Generating Visualizations ===
python .\scripts\generate_visualization.py

echo.
echo ========================================
echo All scenarios completed! Results are in the results/ directory
echo ========================================
