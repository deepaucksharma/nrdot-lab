# Process-Sample Cost Lab

This repository contains a containerized lab environment for optimizing New Relic ProcessSample events.

## Prerequisites
- Docker and Docker Compose
- `jq` (for `make validate`)
- `strace` (for debugging, optional)

## Getting Started

1. Copy the environment template and configure your New Relic credentials:
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

## Security Considerations
- **Full-host mount (`/:/host:ro`)**: Provides full metrics but increases the attack surface. Use `min-mounts.yml` for a more secure, restricted setup.
- **Seccomp**: Enabled by default with `SECURE_MODE=true`. Disable with `SECURE_MODE=false` for debugging.

## Running with Minimal Mounts
To use minimal mounts (`/proc` and `/sys` only), run:
```bash
COMPOSE_FILE=docker-compose.yml:overrides/min-mounts.yml make up
```

## Disabling Seccomp
To disable seccomp for debugging:
```bash
COMPOSE_FILE=docker-compose.yml:overrides/seccomp-disabled.yml make up
```

## Re-enabling `docker_stats` (Optional)
To collect container metrics, add to `otel-config.yaml`:
```yaml
receivers:
  docker_stats:
    endpoint: "unix:///var/run/docker.sock"
```
And mount in `docker-compose.yml`:
```yaml
volumes:
  - /var/run/docker.sock:/var/run/docker.sock:ro
```
**Note**: This increases the attack surface. Use with caution.

## Running the Smoke Test
To verify the lab is working correctly:
```bash
make smoke
```

## Cleanup
To remove all containers and volumes:
```bash
make clean
```