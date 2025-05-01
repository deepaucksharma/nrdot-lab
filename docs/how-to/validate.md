# Validating Cost Optimization

This guide explains how to validate the cost savings achieved with the ProcessSample Optimization Lab and how to interpret the results.

## Quick Validation

For a quick assessment of your optimization results:

```bash
make validate
```

This command runs the `scripts/validate_ingest.sh` script, which:
1. Queries the New Relic API for ProcessSample events
2. Calculates the estimated GB/day and GB/month
3. Compares against a baseline to show reduction percentage

## Understanding the Results

The validation script provides several key metrics:

```
RESULTS:
--------------------------
ProcessSample Events: 1245
Estimated GB/day: 0.15
Estimated GB/month: 4.5
Reduction vs baseline: 73%
--------------------------
```

- **ProcessSample Events**: Total events for the time period
- **Estimated GB/day**: Projected daily ingest volume
- **Estimated GB/month**: Projected monthly ingest volume
- **Reduction vs baseline**: Percentage reduction compared to default configuration

## Running Detailed Analysis

For more comprehensive analysis:

```bash
./scripts/validate_ingest.sh --detailed --time-window 60
```

Options:
- `--detailed`: Provides process-level breakdown
- `--time-window N`: Sets time window to N minutes (default: 30)
- `--baseline`: Compares against standard baseline
- `--output-json`: Outputs results in JSON format

## Validating with NRQL Queries

You can also use the following NRQL queries in New Relic to validate your results:

### 1. Volume by Process Name

```sql
SELECT bytecountestimate()/1e9 as 'GB' 
FROM ProcessSample 
FACET processDisplayName 
LIMIT 10 
SINCE 1 hour ago
```

### 2. Process Resource Usage

```sql
SELECT average(cpuPercent), average(memoryResidentSizeBytes)/1024/1024 as 'Memory (MB)' 
FROM ProcessSample 
FACET processDisplayName 
LIMIT 10 
SINCE 1 hour ago
```

### 3. ProcessSample Event Rate

```sql
SELECT count(*)/60 as 'Events per minute' 
FROM ProcessSample 
TIMESERIES 
SINCE 1 hour ago
```

## Creating a New Relic Dashboard

For ongoing monitoring, create a dashboard in New Relic:

1. Go to New Relic One > Dashboards > Create a dashboard
2. Add the following widgets:
   - ProcessSample event count (timeseries)
   - Estimated GB per day (gauge)
   - Top processes by count (table)
   - Top processes by size (table)

You can use the provided queries as a starting point.

## Measuring ROI

To calculate the return on investment:

1. Run the lab in baseline mode (20s interval, no filtering)
2. Record the GB/month figure
3. Run in optimized mode (60s interval, with filtering)
4. Record the new GB/month figure
5. Calculate savings:
   ```
   monthly_savings = (baseline_GB - optimized_GB) * cost_per_GB
   ```

Where `cost_per_GB` is your New Relic data ingest cost per GB.

## Long-Term Validation

For long-term validation across multiple hosts:

1. Deploy the optimized configuration to production hosts
2. Create a New Relic dashboard to track ProcessSample volume over time
3. Set up alerts for unexpected volume increases
4. Review data weekly to ensure optimization remains effective

## Troubleshooting Validation Issues

### No Events Found

If the validation script returns "No events found":

1. Ensure your license key is correct in `.env`
2. Verify the containers are running with `docker ps`
3. Check the logs with `make logs`
4. Verify your API key has query permissions

### Unexpected Volume

If volume is higher than expected:

1. Verify the sample rate is set to 60 seconds
2. Check that process filtering is working correctly
3. Look for abnormal process activity in the host

### Low Reduction Percentage

If reduction is lower than the expected 70%:

1. Verify all optimization strategies are enabled
2. Check for processes that may be bypassing filters
3. Compare with baseline to ensure proper measurement