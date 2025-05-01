# Quick-start Guide

Get up and running with the ProcessSample Optimization Lab in just 90 seconds.

## Prerequisites

- Docker and Docker Compose
- `jq` (for validation)
- New Relic account with:
  - License key
  - User API key
  - Account ID

## 3-Step Setup

### 1. Configure New Relic Credentials

```bash
cp .env.example .env
# Edit .env with your license key, API key, and account ID
```

### 2. Start the Lab Environment

```bash
make up
```

### 3. Validate Your Results

After running for at least 5 minutes:

```bash
make validate
```

You should see approximately 70% reduction in ProcessSample ingestion volume compared to the default configuration.

## Essential Commands

| Command | Description |
|---------|-------------|
| `make up` | Start all containers |
| `make down` | Stop and remove containers |
| `make logs` | View container logs |
| `make validate` | Check ProcessSample ingest volume |
| `make clean` | Remove containers and volumes |

## Next Steps

- Learn about [optimization concepts](concepts.md)
- Explore alternative [lab scenarios](scenarios.md)
- See detailed [installation instructions](how-to/install.md)