# Infrastructure Events vs. OpenTelemetry Metrics

This comparison helps you understand the differences between New Relic Infrastructure ProcessSample events and OpenTelemetry hostmetrics.

## Side-by-Side Comparison

| Aspect | ProcessSample Events | OpenTelemetry Hostmetrics |
|--------|----------------------|---------------------------|
| **Default Collection Frequency** | 20 seconds | 10 seconds |
| **Optimized Collection Frequency** | 60 seconds | 10 seconds |
| **Cardinality** | One event per process | One metric series per host |
| **Data Volume** | High (especially with many processes) | Low to moderate |
| **Granularity** | Process-level | System-level |
| **CPU Metrics** | Process CPU % | System CPU utilization, by state |
| **Memory Metrics** | Process resident memory | System memory usage, free, cached |
| **Process Details** | Command line, PID, user, etc. | No process-specific data |
| **Cost Impact** | Major contributor to data ingest | Minimal data ingest impact |
| **Query Language** | NRQL | NRQL or Prometheus QL |
| **Dashboard Support** | Full New Relic One support | Full New Relic One support |

## Data Complementarity

When used together with optimized settings:

1. **ProcessSample (60s)**: Provides process-level detail at a reduced frequency
2. **Hostmetrics (10s)**: Provides high-frequency system-level metrics
3. **Combined**: Complete visibility with optimized cost

## Example Use Cases

### When to Rely on ProcessSample

- Troubleshooting specific process issues
- Identifying resource-intensive processes
- Monitoring critical application processes
- When process-level attribution is required

### When to Rely on Hostmetrics

- System-wide performance monitoring
- High-frequency trend analysis
- Capacity planning
- General health monitoring

## Implementation Strategy

The recommended approach is to:

1. Configure ProcessSample at 60s interval with filtering
2. Implement OpenTelemetry hostmetrics at 10s interval
3. Create dashboards that leverage both data sources
4. Set alerts primarily on hostmetrics (higher frequency)
5. Use ProcessSample for deeper investigation when needed

This strategy delivers approximately 70% cost reduction while maintaining or even improving observability capabilities.