# Lab Scenarios

The ProcessSample Optimization Lab supports multiple configurations for different requirements.

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

## Minimal-Mounts Scenario

**Use case**: High-security environments with limited filesystem access

**Configuration**: Limits filesystem access to only `/proc` and `/sys`

```bash
COMPOSE_FILE=docker-compose.yml:overrides/min-mounts.yml make up
```

**Key differences**:
- No filesystem/disk metrics available
- Significantly reduced attack surface
- Same cost savings as Standard Lab

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

**Security note**: Exposes Docker socket to the container (increased attack surface)

## Seccomp-Off Scenario

**Use case**: Debugging seccomp-related issues

**Configuration**: Disables seccomp profile restrictions

```bash
COMPOSE_FILE=docker-compose.yml:overrides/seccomp-disabled.yml make up
```

**When to use**:
- If you encounter "seccomp blocked syscall" errors
- When testing new Infrastructure Agent features
- For identifying syscalls needed for new functionality

**Security note**: Only use temporarily for debugging

## Scenario Comparison

| Scenario | Sample Rate | Process Filtering | Seccomp | Docker Socket | Filesystem Access |
|----------|-------------|-------------------|---------|---------------|-------------------|
| Standard | 60s | Yes | Enabled | No | Full host |
| Minimal-Mounts | 60s | Yes | Enabled | No | Limited to /proc, /sys |
| Docker-Stats | 60s | Yes | Enabled | Yes | Full host |
| Seccomp-Off | 60s | Yes | Disabled | No | Full host |