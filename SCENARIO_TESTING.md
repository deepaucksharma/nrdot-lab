# ProcessSample Testing Scenarios

This document outlines the available testing scenarios and how to run them.

## Available Scenarios

| Category | Scenarios | Purpose |
|----------|-----------|---------|
| Baseline | A-0, A-1, A-2 | Establish baseline and basic optimization |
| Sample Rate | R-20, R-30, R-60, R-90, R-120 | Test different sample rates |
| Filtering | F-none, F-standard, F-aggressive, F-targeted | Compare filtering strategies |
| OpenTelemetry | M-0, M-5, M-10, M-20, M-docker | Analyze OTel contribution |
| Event Size | C-off, C-on | Test command line collection impact |
| Load Testing | L-light, L-heavy, L-io | Test under different loads |

## Running Scenarios

### Windows

```powershell
# Run a single scenario
.\process-lab.ps1 baseline
.\process-lab.ps1 filter-aggressive

# Run all scenarios
.\run_all_scenarios.bat
```

### Linux/macOS

```bash
# Run a single scenario
make baseline
make filter-aggressive

# Run all scenarios
./scripts/run_all_scenarios.sh
```

### Manual Scenario Configuration

```bash
# Windows
.\process-lab.ps1 up -FilterType aggressive -SampleRate 60 -DockerStats

# Linux/macOS
FILTER_TYPE=aggressive SAMPLE_RATE=60 ENABLE_DOCKER_STATS=true make up
```

## Results and Visualization

Results are stored in the `results/` directory with timestamps:

```
results/
  YYYYMMDD_HHMMSS/
    scenario-name.json     # Validation results
    scenario-name_docker_stats.txt   # Resource usage
```

Generate visualizations with:

```bash
# Windows
.\process-lab.ps1 visualize

# Linux/macOS
make visualize
```

## Interpreting Results

The key metrics to analyze:

- **PS_GB_DAY**: Daily ProcessSample data volume
- **VIS_DELAY_S**: Visibility delay in seconds
- **METRIC_GB_DAY**: Daily metric data volume from OpenTelemetry
- **TOTAL_GB_DAY**: Combined data volume

The main goal is to find the optimal balance between cost reduction and observability quality. The recommended configuration is:

- Sample Rate: 60 seconds
- Filter Type: Aggressive
- OTel Interval: 10 seconds