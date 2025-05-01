# Changelog

All notable changes to the New Relic ProcessSample Optimization Lab will be documented in this file.

## [Unreleased]
- Temporarily removed process filtering configuration due to version compatibility issues
- Added Docker stats collection capabilities via docker-stats.yml override
- Updated OpenTelemetry configuration to include docker_stats receiver
- Improved documentation with troubleshooting details for process filtering
- Updated configurations to properly use environment variables from .env file
- Added known issues section to README
- Verified seccomp security profile configuration
- Updated documentation to match actual configuration

## [1.0.0] - Initial Release
- ProcessSample optimization configuration with 60-second interval
- OpenTelemetry integration for system metrics
- Synthetic load generator
- Validation and testing scripts
- Security profiles and container hardening
