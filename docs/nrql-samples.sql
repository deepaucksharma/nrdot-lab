-- Process Sample Cost Analysis Queries

-- Estimate total ProcessSample ingest per day in GB
SELECT bytecountestimate()/1e9 AS 'GB per day' 
FROM ProcessSample SINCE 1 day AGO 
LIMIT MAX

-- Top 10 processes by CPU usage
SELECT average(cpuPercent) AS 'CPU %', processDisplayName 
FROM ProcessSample 
WHERE entityName = 'YOUR_HOST_NAME' 
FACET processDisplayName 
LIMIT 10

-- Top 10 processes by memory usage
SELECT average(memoryResidentSizeBytes)/1024/1024 AS 'Memory (MB)', processDisplayName 
FROM ProcessSample 
WHERE entityName = 'YOUR_HOST_NAME' 
FACET processDisplayName 
LIMIT 10

-- Process count over time
SELECT uniqueCount(processId) AS 'Process Count' 
FROM ProcessSample 
WHERE entityName = 'YOUR_HOST_NAME' 
TIMESERIES 10 minutes

-- Process events per minute (to verify sample rate)
SELECT count(*) / 60 AS 'Events per Minute' 
FROM ProcessSample 
WHERE entityName = 'YOUR_HOST_NAME' 
SINCE 1 hour AGO 
TIMESERIES 10 minutes

-- Process samples by hostname
SELECT count(*) AS 'Sample Count', entityName 
FROM ProcessSample 
FACET entityName 
SINCE 1 day AGO 
LIMIT 20

-- Average event size estimation
SELECT bytecountestimate()/count(*) AS 'Avg Bytes per Event' 
FROM ProcessSample 
SINCE 1 day AGO 
LIMIT MAX

-- Identify processes with high command line length (potential for optimization)
SELECT average(commandLine.length) AS 'Avg CmdLine Length', processDisplayName 
FROM ProcessSample 
WHERE entityName = 'YOUR_HOST_NAME' 
FACET processDisplayName 
LIMIT 20