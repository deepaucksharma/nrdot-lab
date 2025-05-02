# ProcessSample Cost Optimization Testing

This document provides instructions for running the ProcessSample cost optimization experiments both locally and in CI.

## Local Testing

### Prerequisites

1. Docker and Docker Compose installed
2. Python 3.6+ with matplotlib and numpy installed
3. New Relic account with license key and API key
4. PowerShell (for Windows) or Bash (for Linux/Mac)

### Setup

1. Edit the `.env` file to include your New Relic credentials:

```
NEW_RELIC_LICENSE_KEY=your_license_key_here
NEW_RELIC_API_KEY=your_api_key_here  
NR_ACCOUNT_ID=your_account_id_here
```

2. For Windows, you can also edit the `run_all_scenarios.bat` file to include these values directly.

### Running All Scenarios

#### Windows

```
.\run_all_scenarios.bat
```

This will run a shortened version of all scenario categories, with each test running for about 10 minutes.

#### Linux/Mac

```bash
# Make scripts executable
chmod +x scripts/*.sh

# Run the shell version
./scripts/run_all_scenarios.sh
```

### Running Individual Scenarios

You can run individual scenarios using the Makefile targets or directly with the run_one script:

#### Using Makefile (Linux/Mac/Windows with make)

```bash
# Run baseline tests
make baseline
make lab-baseline
make lab-opt

# Run sample rate sweep
make rate-sweep

# Run other categories
make filter-matrix
make otel-study
make event-size
make load-light
make load-heavy
make load-io
```

#### Using run_one script directly

Windows:
```powershell
# Example: Run the baseline test
powershell -Command ".\scripts\run_one.ps1 -SCEN 'A-0' -PROFILE 'bare-agent' -SAMPLE 20 -DURATION 30"
```

Linux/Mac:
```bash
# Example: Run the baseline test
SCEN=A-0 PROFILE=bare-agent SAMPLE=20 DURATION=30 ./scripts/run_one.sh
```

## CI Integration

The repository includes a GitHub Actions workflow configuration in `.github/workflows/scenario-matrix.yml` that runs all test scenarios in a matrix on a nightly schedule.

### GitHub Actions Setup

1. Add the following secrets to your GitHub repository:
   - `NEW_RELIC_LICENSE_KEY`
   - `NEW_RELIC_API_KEY`
   - `NR_ACCOUNT_ID`
   - `SLACK_WEBHOOK_URL` (optional, for notifications)

2. The workflow will:
   - Run different scenario groups in parallel
   - Save results as artifacts
   - Generate visualizations
   - Compare results with the previous night's run
   - Post a summary to Slack (if configured)

### Manual Trigger

You can also manually trigger the workflow from the GitHub Actions UI using the "workflow_dispatch" event.

## Results and Visualization

All test results are stored in the `results/` directory with timestamps. The structure is:

```
results/
  YYYYMMDD_HHMMSS/
    A-0.json         # Scenario results
    A-0_docker_stats.txt   # Resource usage
    A-1.json
    ...
  visualizations/    # Generated after running visualize
    YYYYMMDD_HHMMSS/
      ingest_vs_rate_*.png
      cost_vs_visibility_*.png
```

Run the visualization script to generate plots:

```bash
# Windows
python .\scripts\generate_visualization.py

# Linux/Mac
python3 ./scripts/generate_visualization.py
```

## Interpreting Results

See `docs/experiments.md` for detailed information about each scenario, expected outcomes, and how to interpret the results.

The key metrics to look for:
- **PS_GB_DAY**: Daily ProcessSample data volume
- **VIS_DELAY_S**: Visibility delay in seconds
- **METRIC_GB_DAY**: Daily Metric data volume from OpenTelemetry
- Agent resource usage (CPU/Memory)

The main goal is to find the optimal balance between cost reduction and observability quality.
