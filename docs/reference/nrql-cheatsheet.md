# NRQL Cheatsheet for ProcessSample Analysis

This page contains useful NRQL queries for analyzing ProcessSample data and measuring the effectiveness of optimization strategies.

## Cost Analysis

```sql
-- Estimate total ProcessSample ingest per day in GB
SELECT bytecountestimate()/1e9 AS 'GB per day' 
FROM ProcessSample SINCE 1 day AGO 
LIMIT MAX
```

## Performance Monitoring

### CPU Usage Analysis

```sql
-- Top 10 processes by CPU usage
SELECT average(cpuPercent) AS 'CPU %', processDisplayName 
FROM ProcessSample 
WHERE entityName = 'YOUR_HOST_NAME' 
FACET processDisplayName 
LIMIT 10
```

### Memory Usage Analysis

```sql
-- Top 10 processes by memory usage
SELECT average(memoryResidentSizeBytes)/1024/1024 AS 'Memory (MB)', processDisplayName 
FROM ProcessSample 
WHERE entityName = 'YOUR_HOST_NAME' 
FACET processDisplayName 
LIMIT 10
```

## System Monitoring

### Process Count Tracking

```sql
-- Process count over time
SELECT uniqueCount(processId) AS 'Process Count' 
FROM ProcessSample 
WHERE entityName = 'YOUR_HOST_NAME' 
TIMESERIES 10 minutes
```

### Sample Rate Verification

```sql
-- Process events per minute (to verify sample rate)
SELECT count(*) / 60 AS 'Events per Minute' 
FROM ProcessSample 
WHERE entityName = 'YOUR_HOST_NAME' 
SINCE 1 hour AGO 
TIMESERIES 10 minutes
```

## Environment Analysis

### Host Distribution

```sql
-- Process samples by hostname
SELECT count(*) AS 'Sample Count', entityName 
FROM ProcessSample 
FACET entityName 
SINCE 1 day AGO 
LIMIT 20
```

## Optimization Opportunities

### Event Size Analysis

```sql
-- Average event size estimation
SELECT bytecountestimate()/count(*) AS 'Avg Bytes per Event' 
FROM ProcessSample 
SINCE 1 day AGO 
LIMIT MAX
```

### Command Line Optimization

```sql
-- Identify processes with high command line length (potential for optimization)
SELECT average(commandLine.length) AS 'Avg CmdLine Length', processDisplayName 
FROM ProcessSample 
WHERE entityName = 'YOUR_HOST_NAME' 
FACET processDisplayName 
LIMIT 20
```

## Tips for Effective Queries

1. Replace `'YOUR_HOST_NAME'` with your actual host name or use a FACET clause instead
2. Adjust the time range (`SINCE 1 day AGO`) based on your data retention and analysis needs
3. Use `TIMESERIES` for trend analysis and `FACET` for dimensional analysis
4. The `bytecountestimate()` function provides an approximation of data volume