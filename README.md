# New Relic ProcessSample Optimization Lab

This repository contains a containerized lab environment for optimizing New Relic ProcessSample events cost without sacrificing observability. The lab demonstrates how to achieve approximately 70% reduction in ProcessSample ingestion volume through a combination of sampling rate adjustments, filtering, and alternative metrics sources.

## Prerequisites

- Docker and Docker Compose
- `jq` (for `make validate`)
- `strace` (for debugging, optional)
- New Relic account with:
  - License key
  - User API key (for validation)
  - Account ID

## Getting Started

1. Configure your New Relic credentials:
   ```bash
   cp .env.example .env
   # Edit .env with your license key, API key, and account ID
   ```

2. Launch the lab environment:
   ```bash
   make up
   ```

3. Monitor the logs:
   ```bash
   make logs
   ```

4. Check ingestion statistics:
   ```bash
   make validate
   ```

5. Stop the lab:
   ```bash
   make down
   ```

## Available Commands

| Command | Description |
|---------|-------------|
| `make up` | Start all containers |
| `make down` | Stop and remove containers |
| `make logs` | View container logs |
| `make validate` | Check ProcessSample ingest volume |
| `make clean` | Remove containers and volumes |
| `make smoke` | Run CI smoke tests |
| `make help` | Show available commands |

## Lab Scenarios

The lab supports multiple configurations for different requirements:

### 1. Standard Lab (Default)
```bash
make up
```
- 60-second ProcessSample interval
- Process filtering enabled
- Full host metrics available
- Seccomp security profile enforced

### 2. Minimal-Mounts Mode
```bash
COMPOSE_FILE=docker-compose.yml:overrides/min-mounts.yml make up
```
- Only mounts `/proc` and `/sys`
- No disk/filesystem metrics
- Highest security posture

### 3. Seccomp-Off Troubleshooting
```bash
COMPOSE_FILE=docker-compose.yml:overrides/seccomp-disabled.yml make up
```
- Disabled seccomp profile
- For debugging "seccomp blocked syscall" errors
- Reduced security (for troubleshooting only)

### 4. Container Metrics (docker_stats)
To enable container metrics collection:

1. Add to `otel-config.yaml`:
   ```yaml
   receivers:
     docker_stats:
       endpoint: "unix:///var/run/docker.sock"
   ```

2. Add to `otel` service in `docker-compose.yml`:
   ```yaml
   volumes:
     - /var/run/docker.sock:/var/run/docker.sock:ro
   ```

**Note**: This increases the attack surface. Use with caution.

## Security Considerations

- **Full-host mount (`/:/host:ro`)**: The default configuration mounts the entire host filesystem to provide complete metrics. Use `min-mounts.yml` for a more secure setup.
- **Seccomp profiles**: Restrict container syscalls to a minimal allowed set. Can be disabled for debugging.
- **Read-only filesystems**: All volumes are mounted read-only with tmpfs for writable directories.

## Optimization Strategy

The lab implements three core strategies:

1. **Throttled Sample Rate**: Increases the interval from 20s to 60s (~67% reduction)
2. **Process Filtering**: Excludes non-essential process metrics (~5-10% additional reduction)
3. **OpenTelemetry Hostmetrics**: Provides alternative system-level metrics at 10s intervals

For detailed guidance, troubleshooting, and additional scenarios, see the [lab guide](docs/lab-guide.md).
