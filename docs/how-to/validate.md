# Validation Guide

## Basic Validation

Run the validation script:

```bash
make validate
```

Example output:

```
RESULTS:
--------------------------
ProcessSample Events: 1245
Estimated GB/day: 0.15
Estimated GB/month: 4.5
Reduction vs baseline: 73%
--------------------------
```

## Detailed Analysis

```bash
./scripts/validate_ingest.sh --detailed --time-window 60
```

Options:
- `--detailed`: Process-level breakdown
- `--time-window N`: Sets time window in minutes
- `--baseline`: Compares against baseline
- `--output-json`: JSON format output

## Key NRQL Queries

### Volume Analysis

```sql
SELECT bytecountestimate()/1e9 as 'GB' 
FROM ProcessSample 
SINCE 1 hour ago
```

### Events Per Minute

```sql
SELECT count(*)/60 as 'Events per minute' 
FROM ProcessSample 
TIMESERIES 
SINCE 1 hour ago
```

### Top Processes by Volume

```sql
SELECT bytecountestimate()/1e9 as 'GB' 
FROM ProcessSample 
FACET processDisplayName 
LIMIT 10 
SINCE 1 hour ago
```

## ROI Calculation

```
monthly_savings = (baseline_GB - optimized_GB) * cost_per_GB
```