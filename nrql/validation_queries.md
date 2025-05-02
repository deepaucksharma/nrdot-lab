# NRQL Queries for Validation

This document contains common NRQL queries used by the validation module to verify configuration effectiveness.

## Process Sample Data Ingest

### Query Actual Ingest Rate by Host

```sql
FROM NrConsumption 
SELECT sum(bytesIngested)/1024/1024/1024 as giBIngested 
WHERE metricName='ProcessSample' AND (hostname = '$HOST' OR hostname IN ($HOSTS))
FACET hostname
SINCE $TIMEFRAME HOURS AGO
```

Use this query to determine the actual data ingest for process monitoring on specific hosts.

### Query Process Sample Count by Host

```sql
FROM ProcessSample 
SELECT count(*) 
WHERE hostname = '$HOST'
SINCE $TIMEFRAME HOURS AGO
TIMESERIES
```

Use this query to check if process samples are being collected at the expected frequency.

### Query Filtered Process Count

```sql
FROM ProcessSample 
SELECT uniqueCount(processId) 
WHERE hostname = '$HOST'
SINCE $TIMEFRAME HOURS AGO
```

Use this query to check how many unique processes are being monitored, which helps validate filtering effectiveness.

## Tier-1 Process Coverage

```sql
FROM ProcessSample 
SELECT uniqueCount(processId), uniqueCount(entityGuid) 
WHERE hostname = '$HOST' AND (
  $TIER1_FILTER
)
SINCE $TIMEFRAME HOURS AGO
```

Use this query to verify that critical tier-1 processes are being monitored.

## Sample Rate Verification

```sql
FROM ProcessSample 
SELECT count(*)/uniqueCount(processId) as samplesPerProcess
WHERE hostname = '$HOST'
SINCE $TIMEFRAME HOURS AGO
```

Use this query to verify that the sample rate matches the expected configuration.

## Troubleshooting Queries

### Check for Missing Data

```sql
FROM NrConsumption 
SELECT sum(bytesIngested) 
WHERE metricName='ProcessSample' AND hostname = '$HOST'
TIMESERIES 1 hour
SINCE $TIMEFRAME HOURS AGO
```

Use this query to check for gaps in data collection that might indicate agent issues.

### Check Agent Configuration Status

```sql
FROM NrIntegrationError 
SELECT count(*) 
WHERE hostname = '$HOST' AND integrationName = 'nri-process-discovery'
FACET message
SINCE $TIMEFRAME HOURS AGO
```

Use this query to check for integration errors that might indicate configuration problems.
