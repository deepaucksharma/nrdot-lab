# New Relic ProcessSample Optimization Lab

[![Documentation](https://img.shields.io/badge/docs-online-brightgreen)](https://deepaucksharma.github.io/infra-lab/)
[![CI Status](https://img.shields.io/github/actions/workflow/status/deepaucksharma/infra-lab/ci.yml?branch=master&label=ci)](https://github.com/deepaucksharma/infra-lab/actions)
[![License](https://img.shields.io/badge/license-MIT-blue)](LICENSE)

A containerized lab environment for optimizing New Relic ProcessSample events cost without sacrificing observability.

## 🚀 Key Features

- Achieve ~70% reduction in ProcessSample ingestion volume
- Multiple security posture configurations
- Complete metrics visibility using OpenTelemetry
- Validation scripts to measure real cost savings

## 📊 Core Optimization Strategies

1. **Throttled Sample Rate**: 60s interval instead of 20s (~67% reduction)
2. **Process Filtering**: Exclude non-essential process metrics (~5-10% additional reduction)
3. **OpenTelemetry Hostmetrics**: Alternative system-level metrics at 10s intervals

## 🏁 Quick Start

```bash
# Clone the repository
git clone https://github.com/deepaucksharma/infra-lab.git
cd infra-lab

# Configure credentials
cp .env.example .env
# Edit .env with your New Relic license key, API key, and account ID

# Start the lab
make up

# Check ingestion statistics (after a few minutes)
make validate
```

## 📘 Documentation

[**View the complete documentation**](https://deepaucksharma.github.io/infra-lab/)

The documentation includes:

- [Quick-start guide](https://deepaucksharma.github.io/infra-lab/quickstart/)
- [Concepts and theory](https://deepaucksharma.github.io/infra-lab/concepts/)
- [Detailed scenarios](https://deepaucksharma.github.io/infra-lab/scenarios/)
- [How-to guides](https://deepaucksharma.github.io/infra-lab/how-to/install/)
- [Troubleshooting](https://deepaucksharma.github.io/infra-lab/how-to/troubleshoot/)
- [NRQL reference](https://deepaucksharma.github.io/infra-lab/reference/nrql-cheatsheet/)

## 🛡️ Security Postures

The lab supports multiple security configurations:

| Configuration | Command | Security Level |
|---------------|---------|--------------|
| Standard | `make up` | 🔒 Normal |
| Minimal Mounts | `COMPOSE_FILE=docker-compose.yml:overrides/min-mounts.yml make up` | 🔒🔒 Highest |
| Docker Stats | `COMPOSE_FILE=docker-compose.yml:overrides/docker-stats.yml make up` | 🔓 Reduced (Docker socket access) |
| Seccomp Off | `COMPOSE_FILE=docker-compose.yml:overrides/seccomp-disabled.yml make up` | ⚠️ For debugging only |

## 📋 Prerequisites

- Docker and Docker Compose
- `jq` (for validation scripts)
- New Relic account with license key, user API key, and account ID

## 📦 Recent Updates

- Added Docker stats collection capability
- Enhanced documentation with MkDocs Material theme
- Improved process filtering configuration

For the complete change history, see the [Changelog](https://deepaucksharma.github.io/infra-lab/changelog/)