# Installation Guide

## Prerequisites

- Docker 20.10.0+
- Docker Compose 2.0.0+
- jq (for validation)
- New Relic account (license key, API key, account ID)

## Installation Steps

### 1. Configure Environment

```bash
cp .env.example .env
```

Edit `.env` with your credentials:

```ini
NEW_RELIC_LICENSE_KEY=your_license_key
NEW_RELIC_API_KEY=your_user_api_key
NR_ACCOUNT_ID=your_account_id
```

### 2. Start the Lab

Standard configuration:

```bash
make up
```

Alternative configurations:

```bash
# Enhanced security
COMPOSE_FILE=docker-compose.yml:overrides/min-mounts.yml make up

# Container metrics
COMPOSE_FILE=docker-compose.yml:overrides/docker-stats.yml make up

# Troubleshooting
COMPOSE_FILE=docker-compose.yml:overrides/seccomp-disabled.yml make up
```

### 3. Monitor & Validate

View logs:

```bash
make logs
```

Validate results (after 5+ minutes):

```bash
make validate
```

### 4. Stopping the Lab

```bash
make down    # Stop containers
make clean   # Remove containers and volumes
```