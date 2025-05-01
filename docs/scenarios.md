# Lab Scenarios

The ProcessSample Optimization Lab supports multiple configurations for different requirements. Each scenario demonstrates specific optimization techniques and security considerations.

## Standard Scenario

**Use case**: General cost optimization with balanced security

**Configuration**: Default setup with 60s sample rate, process filtering, and seccomp security profile

```bash
make up
```

**Expected outcomes**:
- ~70% reduction in ProcessSample ingest
- Full visibility into host metrics
- Strong security posture

**Example output**:

```
Starting ProcessSample Lab...
Creating network "process_default" with the default driver
Creating process_load_1  ... done
Creating process_otel_1  ... done
Creating process_infra_1 ... done
```

**Validation**:

```bash
make validate
```

```
Calculating ProcessSample ingest volume...
Querying New Relic API for the last 30 minutes...

RESULTS:
--------------------------
ProcessSample Events: 1245
Estimated GB/day: 0.15
Estimated GB/month: 4.5
Reduction vs baseline: 73%
--------------------------
```

## Minimal-Mounts Scenario

**Use case**: High-security environments with limited filesystem access requirements

**Configuration**: Limits filesystem access to only `/proc` and `/sys`

```bash
COMPOSE_FILE=docker-compose.yml:overrides/min-mounts.yml make up
```

**Key differences**:
- No filesystem/disk metrics available
- Significantly reduced attack surface
- Same cost savings as Standard Lab

**Security benefits**:
- Minimal host filesystem exposure
- Reduced privilege escalation risk
- Compliant with strict security policies

## Seccomp-Off Scenario

**Use case**: Debugging seccomp-related issues or testing new agent features

**Configuration**: Disables seccomp profile restrictions, allowing all syscalls

```bash
COMPOSE_FILE=docker-compose.yml:overrides/seccomp-disabled.yml make up
```

**When to use**:
- If you encounter "seccomp blocked syscall" errors
- When testing new Infrastructure Agent features
- For identifying syscalls needed for new functionality

**Security note**:
Only use temporarily for debugging, then return to a secured configuration.

## Docker-Stats Scenario

**Use case**: When detailed container-level metrics are required

**Configuration**: Adds Docker socket mount and configures the docker_stats receiver

```bash
COMPOSE_FILE=docker-compose.yml:overrides/docker-stats.yml make up
```

**Additional metrics**:
- Container CPU usage
- Container memory usage
- Container network I/O
- Container block I/O

**Security implications**:
- Exposes Docker socket to the container
- Significantly increases the attack surface
- Use only when container metrics are essential

## Baseline Scenario

**Use case**: Establishing a baseline for comparison or cost justification

**Configuration**: Uses default 20s interval with no filtering

**Manual setup**:
1. Edit `config/newrelic-infra.yml`:
   ```yaml
   metrics_process_sample_rate: 20  # Change from 60 to 20
   # Comment out the exclude_matching_metrics section
   ```

2. Run the lab and validate:
   ```bash
   make up
   # Wait 5+ minutes
   make validate
   ```

**Purpose**:
- Demonstrates unoptimized ingest volume
- Provides comparison for ROI calculations
- Helps justify the optimization effort

## Scenario Comparison Matrix

| Scenario | Sample Rate | Process Filtering | Seccomp | Docker Socket | Filesystem Access |
|----------|-------------|-------------------|---------|---------------|-------------------|
| Standard | 60s | Yes | Enabled | No | Full host |
| Minimal-Mounts | 60s | Yes | Enabled | No | Limited to /proc, /sys |
| Seccomp-Off | 60s | Yes | Disabled | No | Full host |
| Docker-Stats | 60s | Yes | Enabled | Yes | Full host |
| Baseline | 20s | No | Enabled | No | Full host |

## Choosing the Right Scenario

1. **Starting point**: Begin with the Standard Scenario to understand the basic optimization techniques
2. **Production use**: Consider Minimal-Mounts Scenario for production environments with strict security requirements
3. **Troubleshooting**: Use Seccomp-Off Scenario temporarily if you encounter security-related issues
4. **Container monitoring**: Add Docker-Stats Scenario only when container-specific metrics are required
5. **Cost justification**: Run Baseline Scenario measurements to demonstrate the value of optimization