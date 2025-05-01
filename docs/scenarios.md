# Lab Scenarios

The ProcessSample Optimization Lab supports multiple configurations for different requirements.

## Standard Scenario

**Use case**: General cost optimization

**Configuration**: Default setup with 60s sample rate and process filtering

```bash
make up
```

**Expected outcomes**:
- ~70% reduction in ProcessSample ingest
- Full visibility into host metrics

## Docker-Stats Scenario

**Use case**: When detailed container-level metrics are required

**Configuration**: Adds Docker socket mount and configures the docker_stats receiver

```bash
make docker-stats
```

**Additional metrics**:
- Container CPU usage
- Container memory usage
- Container network I/O
- Container block I/O

## Scenario Comparison

| Scenario | Sample Rate | Process Filtering | Docker Socket |
|----------|-------------|-------------------|---------------|
| Standard | 60s | Yes | No |
| Docker-Stats | 60s | Yes | Yes |