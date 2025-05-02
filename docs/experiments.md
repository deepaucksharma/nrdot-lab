# ProcessSample Cost Optimization Experiments

This document outlines the experimental scenarios designed to find the optimal balance between ProcessSample costs and observability effectiveness.

## Guiding Metrics

| Name | Formula | Where to Pull |
|------|---------|---------------|
| **PS_GB_DAY** | `bytecountestimate()/1e9` over 24 h | NRQL on `ProcessSample` |
| **METRIC_GB_DAY** | `bytecountestimate()/1e9` over 24 h | NRQL on **Metric** (filter: `metricName LIKE 'system.%'`) |
| **VIS_DELAY_S** | wall-clock seconds from synthetic spike ➜ first visible spike in NR dashboard | Automatically calculated |
| **AGENT_CPU% / MEM_MB** | `docker stats` or `otel docker_stats` | Automatically captured |

## Scenario Categories

### Category 1: Baseline & Core-Opt

Establishes baseline metrics and initial optimization targets.

| Scenario ID | Description | Override Files | Expected KPI |
|-------------|-------------|----------------|--------------|
| **A-0** `bare-agent` | Baseline with no OTel service | `profiles/bare-agent.yml` | Anchor cost |
| **A-1** `lab-baseline` | Default lab setup | Default profiles | Shows OTel overhead |
| **A-2** `lab-opt` | Optimized default setup | Default with filters | ≈ 70% ↓ PS_GB_DAY |

### Category 2: Sample-Rate Sweep

Tests the impact of different sample rates on cost and visibility.

| Scenario ID | Description | Key Variable | Expected Impact |
|-------------|-------------|--------------|----------------|
| **R-20** | 20s sample rate | `metrics_process_sample_rate: 20` | Baseline cost |
| **R-30** | 30s sample rate | `metrics_process_sample_rate: 30` | ≈ 33% ↓ PS_GB_DAY |
| **R-60** | 60s sample rate | `metrics_process_sample_rate: 60` | ≈ 66% ↓ PS_GB_DAY |
| **R-90** | 90s sample rate | `metrics_process_sample_rate: 90` | ≈ 77% ↓ PS_GB_DAY |
| **R-120** | 120s sample rate | `metrics_process_sample_rate: 120` | ≈ 83% ↓ PS_GB_DAY |

### Category 3: Filtering Matrix

Evaluates different process filtering strategies.

| Scenario ID | Description | Override Files | Expected Impact |
|-------------|-------------|----------------|----------------|
| **F-none** | No filtering | `overrides/filters/none.yml` | Maximum cost, full visibility |
| **F-current** | Current filters | `overrides/filters/current.yml` | Moderate cost reduction |
| **F-aggressive** | Extended filter list | `overrides/filters/aggressive.yml` | Significant cost reduction |
| **F-targeted** | Inclusion filtering | `overrides/filters/targeted.yml` | Maximum cost reduction, limited visibility |

### Category 4: OTel Contribution Study

Analyzes OpenTelemetry's impact on metrics and costs.

| Scenario ID | Description | Configuration Files | Key Metrics |
|-------------|-------------|---------------------|------------|
| **M-0** | No OTel | N/A | Baseline METRIC_GB_DAY |
| **M-5** | OTel 5s interval | `config/otel-5s.yaml` | Higher granularity, higher cost |
| **M-10** | OTel 10s interval (current) | `config/otel-config.yaml` | Current baseline |
| **M-20** | OTel 20s interval | `config/otel-20s.yaml` | Lower cost, reduced granularity |
| **M-scr-lite** | Only CPU/memory scrapers | `config/otel-scr-lite.yaml` | Reduced metrics variety |
| **M-docker** | Docker metrics enabled | docker-stats profile | Added container metrics |

### Category 5: Event Size Impact

Tests how command line collection affects event size and costs.

| Scenario ID | Description | Configuration | Expected Impact |
|-------------|-------------|---------------|----------------|
| **C-off** | Command line off (current) | `collect_process_commandline: false` | Baseline |
| **C-on** | Command line collection on | `collect_process_commandline: true` | Increased event size |
| **C-strip** | Command line stripped | `collect_process_commandline: true` + `strip_command_line: true` | Moderate increase |

### Category 6: Load Robustness

Tests how system load affects metrics collection and costs.

| Scenario ID | Description | Environment Variables | Focus Area |
|-------------|-------------|------------------------|-----------|
| **L-light** | Light load | `STRESS_CPU=1 STRESS_MEM=64M` | Baseline performance |
| **L-heavy** | Heavy load | `STRESS_CPU=8 STRESS_MEM=1G` | High CPU/memory impact |
| **L-io** | IO-focused load | `LOAD_STRESSOR="--hdd 1"` | IO subsystem impact |

## Running Experiments

Experiments can be run individually or in categories using the Makefile targets:

```bash
# Run baseline tests
make baseline
make lab-baseline
make lab-opt

# Run all sample rate tests
make rate-sweep

# Test filtering strategies
make filter-matrix

# Test OTel configurations
make otel-study

# Test event size impact
make event-size

# Test under different loads
make load-light
make load-heavy
make load-io

# Generate result visualizations
make visualize
```

## Result Analysis

After running experiments, results are stored in the `results/` directory with timestamps. 
The `make visualize` command generates two key plots:

1. **Ingest vs Sample Rate** - Shows the relationship between sample rate and daily ingest volume
2. **Cost vs Visibility Latency** - Shows the trade-off between cost (GB/day) and visibility delay

These visualizations help determine the optimal configuration that balances cost with observability quality.

## Cost vs Visibility Equation

The fundamental relationship can be expressed as:

```
Cost ∝ f(rate, event size, process count)
Visibility ∝ g(rate, granularity)
```

Optimizing involves finding the sweet spot where cost reduction doesn't significantly degrade observability.