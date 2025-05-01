# NRQL Query Reference

This page contains useful NRQL queries for analyzing ProcessSample data and measuring the effectiveness of optimization strategies.

## Cost Analysis

```sql
-- Daily ProcessSample volume in GB
SELECT bytecountestimate()/1e9 AS 'GB per day' 
FROM ProcessSample SINCE 1 day AGO
```

## Performance Monitoring

```sql
-- Top 10 processes by CPU usage
SELECT average(cpuPercent) AS 'CPU %', processDisplayName 
FROM ProcessSample 
FACET processDisplayName 
LIMIT 10

-- Top 10 processes by memory usage
SELECT average(memoryResidentSizeBytes)/1024/1024 AS 'Memory (MB)' 
FROM ProcessSample 
FACET processDisplayName 
LIMIT 10
```

## System Monitoring

```sql
-- Process count over time
SELECT uniqueCount(processId) AS 'Process Count' 
FROM ProcessSample 
TIMESERIES 10 minutes

-- Sample rate verification
SELECT count(*) / 60 AS 'Events per Minute' 
FROM ProcessSample 
TIMESERIES 10 minutes
```

## Optimization Insights

```sql
-- Average event size
SELECT bytecountestimate()/count(*) AS 'Avg Bytes per Event' 
FROM ProcessSample 
SINCE 1 day AGO

-- Processes with long command lines
SELECT average(commandLine.length) AS 'Avg CmdLine Length'
FROM ProcessSample 
FACET processDisplayName 
LIMIT 20
```

## Full Query Pack

```sql
--8<-- "docs/nrql-samples.sql"
```