# New Relic ProcessSample Optimization Lab

Welcome to the ProcessSample Optimization Lab documentation. This lab provides a containerized environment for optimizing New Relic ProcessSample events cost without sacrificing observability.

## 🎯 What This Lab Demonstrates

This lab demonstrates how to achieve approximately **70% reduction in ProcessSample ingestion volume** through a combination of:
- Sample rate optimization
- Process filtering
- Alternative metrics sources via OpenTelemetry

## 📊 Optimization Strategies

| Strategy | Approach | Estimated Reduction |
|----------|----------|---------------------|
| [**Sample Rate Throttling**](concepts.md#sample-rate-throttling) | Increase interval from 20s to 60s | ~67% |
| [**Process Filtering**](concepts.md#process-filtering) | Exclude non-essential processes | ~5-10% additional |
| [**OpenTelemetry Metrics**](concepts.md#opentelemetry-metrics) | Alternative system metrics at 10s intervals | Preserves visibility |

## 🚀 Getting Started

New to the lab? Follow these steps:

1. [**Quick-start Guide**](quickstart.md) - Get up and running in minutes
2. [**Installation Guide**](how-to/install.md) - Detailed installation instructions
3. [**Validation Guide**](how-to/validate.md) - Verify your optimization results

## 🧪 Lab Scenarios

The lab includes several pre-configured scenarios to explore different optimization approaches:

| Scenario | Description | Security | Documentation |
|----------|-------------|----------|--------------|
| **Standard** | 60s sampling, default settings | Normal | [Details](scenarios.md#standard-scenario) |
| **Minimal-Mounts** | Restricted filesystem access | Enhanced | [Details](scenarios.md#minimal-mounts-scenario) |
| **Docker Stats** | Container metrics integration | Reduced | [Details](scenarios.md#docker-stats-scenario) |
| **Seccomp Off** | For troubleshooting | Debug Only | [Details](scenarios.md#seccomp-off-scenario) |

## 📚 Documentation Structure

This documentation is organized into these main sections:

- **[Concepts](concepts.md)** - Core theory and optimization principles
- **[Scenarios](scenarios.md)** - Pre-configured test scenarios
- **How-to Guides** - Step-by-step instructions
  - [Installation](how-to/install.md)
  - [Validation](how-to/validate.md)
  - [Extension](how-to/extend.md)
  - [Troubleshooting](how-to/troubleshoot.md)
- **Reference** - Technical references
  - [Infrastructure Agent Configuration](reference/newrelic-infra.md)
  - [OpenTelemetry Configuration](reference/otel-config.md)
  - [NRQL Cheatsheet](reference/nrql-cheatsheet.md)
- **Automation**
  - [GitHub Actions](automation/github-actions.md)
  - [Local Scripts](automation/scripts.md)

## 🔬 Test Results

The lab includes automated testing of all scenarios to provide empirical evidence of optimization effectiveness:

- [**Latest Test Results**](latest-results.md) - Most recent automated test run
- Regular tests are scheduled weekly via [GitHub Actions](automation/github-actions.md)

## 💡 Optimization Best Practices

For best results, consider these recommendations:

1. **Start with sample rate adjustment** (60s) for immediate gains
2. **Add process filtering** to exclude non-essential processes
3. **Use OpenTelemetry hostmetrics** for high-frequency system visibility
4. **Validate your results** to confirm actual reduction

## 🔄 Recent Updates

See the [Changelog](changelog.md) for the latest updates and improvements.

## 🛡️ Security Considerations

The lab includes several security-focused configurations:

- **Seccomp profiles** to restrict container syscalls
- **Minimal-mounts mode** for reduced filesystem access
- **Read-only mounts** to prevent filesystem modifications

## 🤝 Contributing

Contributions to this lab are welcome! See our [GitHub repository](https://github.com/deepaucksharma/infra-lab) for more information on how to contribute.
