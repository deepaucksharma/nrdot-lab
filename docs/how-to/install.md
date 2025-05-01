# Installation & Running

This guide provides detailed instructions for installing and running the ProcessSample Optimization Lab.

## Prerequisites

Before you begin, ensure you have the following installed:

- **Docker**: Version 20.10.0 or higher
- **Docker Compose**: Version 2.0.0 or higher
- **jq**: Required for the validation script
- **New Relic account** with:
  - License key (for sending data)
  - User API key (for validation)
  - Account ID

## Installation Steps

### 1. Clone the Repository

```bash
git clone https://github.com/your-org/deepaucksharma-infra-lab.git
cd deepaucksharma-infra-lab
```

### 2. Configure Environment Variables

Create and configure your environment file:

```bash
cp .env.example .env
```

Edit the `.env` file with your New Relic credentials:

```ini
NEW_RELIC_LICENSE_KEY=your_license_key_here
NEW_RELIC_API_KEY=your_user_api_key_here
NR_ACCOUNT_ID=your_account_id_here
```

### 3. Review Configuration (Optional)

Before running, you can review the default configurations:

- **Infrastructure Agent**: `config/newrelic-infra.yml`
- **OpenTelemetry Collector**: `config/otel-config.yaml`
- **Docker Compose**: `docker-compose.yml`

## Running the Lab

### Standard Configuration

To run the lab with the default configuration:

```bash
make up
```

This will:
1. Build and start all containers
2. Configure the Infrastructure Agent with 60s sampling
3. Configure the OpenTelemetry Collector for hostmetrics
4. Start the synthetic load generator

### Alternative Configurations

#### Minimal Mounts Configuration

For enhanced security with limited filesystem access:

```bash
COMPOSE_FILE=docker-compose.yml:overrides/min-mounts.yml make up
```

#### Seccomp Disabled (Troubleshooting)

If you encounter security-related issues:

```bash
COMPOSE_FILE=docker-compose.yml:overrides/seccomp-disabled.yml make up
```

#### Docker Stats Collection

To add container metrics collection:

```bash
COMPOSE_FILE=docker-compose.yml:overrides/docker-stats.yml make up
```

## Monitoring the Lab

### View Container Logs

To monitor the containers in real-time:

```bash
make logs
```

To follow only a specific container:

```bash
docker logs -f process_infra_1
```

### Verify Data Ingestion

After running for at least 5 minutes, verify data is flowing to New Relic:

```bash
make validate
```

You should see output similar to:

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

## Stopping the Lab

To stop and remove the containers:

```bash
make down
```

To completely clean up all resources, including volumes:

```bash
make clean
```

## Next Steps

- Learn how to [validate costs](validate.md) in detail
- Explore [troubleshooting](troubleshoot.md) common issues
- See how to [extend the lab](extend.md) with custom configurations