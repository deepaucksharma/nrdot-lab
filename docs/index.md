# New Relic ProcessSample Optimization Lab

Welcome to the comprehensive documentation for the New Relic ProcessSample Optimization Lab. This lab environment demonstrates how to reduce ProcessSample events cost without sacrificing observability capabilities.

## What You'll Learn

- How to reduce ProcessSample data volume by approximately 70%
- Implementation of multiple optimization strategies
- Alternative metrics sources using OpenTelemetry
- Security considerations for production deployments

## Key Features

- **Cost Optimization**: Techniques to significantly reduce data ingest costs
- **Security**: Containerized environment with security profiles
- **Validation**: Tools to measure and validate cost savings
- **Extensibility**: Framework for testing alternative configurations

## Getting Started

If you're new to the lab, start with the [Quick-start Guide](quickstart.md) to get up and running in minutes.

For a deeper understanding of the optimization problem and solutions, see the [Concepts](concepts.md) page.

## Available Scenarios

The lab supports multiple configurations for different requirements:

| Scenario | Description | Command |
|----------|-------------|---------|
| Standard Lab | Default setup with balanced security | `make up` |
| Minimal-Mounts | Restricted filesystem access | `COMPOSE_FILE=docker-compose.yml:overrides/min-mounts.yml make up` |
| Seccomp-Off | For troubleshooting security issues | `COMPOSE_FILE=docker-compose.yml:overrides/seccomp-disabled.yml make up` |
| Docker Stats | Container metrics collection | `COMPOSE_FILE=docker-compose.yml:overrides/docker-stats.yml make up` |

For detailed descriptions of each scenario, visit the [Scenarios](scenarios.md) page.

## Documentation Structure

- **[Quick-start](quickstart.md)**: Get up and running in minutes
- **[Concepts](concepts.md)**: Understand the optimization problem and solutions
- **[Scenarios](scenarios.md)**: Explore different lab configurations
- **How-to Guides**:
  - [Install & Run](how-to/install.md)
  - [Validate Costs](how-to/validate.md)
  - [Extend the Lab](how-to/extend.md)
  - [Troubleshoot](how-to/troubleshoot.md)
- **Reference**:
  - [OTel Configuration](reference/otel-config.md)
  - [NR Infrastructure Configuration](reference/newrelic-infra.md)
  - [NRQL Cheat-sheet](reference/nrql-cheatsheet.md)