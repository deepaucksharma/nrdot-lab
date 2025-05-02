# Quick Start Guide 🛫

This guide walks through installing the `process-lab` CLI tool and using its core features for generating and analyzing New Relic agent configurations.

> **Prerequisites:**
> *   Python 3.8+ and `pip`
> *   Git
> *   (Optional but Recommended) Docker Engine 20+ & Docker Compose v2+ for local testing using the `compose/` environment.
> *   New Relic **License Key** (required for agent)
> *   New Relic **User API Key** (required for `estimate-cost`, `recommend`, and NRDB-based `lint` features)
> *   New Relic **Account ID** (required for `estimate-cost`, `recommend`)

---

## 1. Installation

```bash
# 1. Clone the repository
git clone https://github.com/deepaucksharma/infra-lab.git
cd infra-lab

# 2. Create and activate a virtual environment (recommended)
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate

# 3. Install the package
pip install .
# For development: pip install -e ".[dev]"

# 4. Verify installation
process-lab --help
```

## 2. Configuration

```bash
# 1. Copy the environment variable template
cp .env.example .env

# 2. Edit the .env file with your credentials
#    - NEW_RELIC_LICENSE_KEY (required for agent testing)
#    - NEW_RELIC_API_KEY (required for NRDB features)
#    - NR_ACCOUNT_ID (required for NRDB features)
$EDITOR .env # Or use your preferred editor
```

The tool reads credentials from this `.env` file or environment variables.

## 3. Core Workflow

The primary interface is the `process-lab` command.

### A. Generate Configuration using Wizard

The wizard guides you through creating a configuration file.

```bash
# Start the interactive wizard
process-lab wizard --output my-first-config.yml

# Answer prompts for sample rate, filter type, etc.
# The wizard will:
# - Generate the YAML file (e.g., my-first-config.yml)
# - Estimate cost (requires API key)
# - Lint for risks (uses NRDB data if API key provided)
# - Optionally generate rollout artifacts
```

**Note:** Always use the `--output` (`-o`) flag to specify a destination for your generated file. Avoid using the default path (`./config/newrelic-infra.yml`) as it will overwrite the example file in the repository.

### B. Generate Configuration using Presets or Flags

Generate non-interactively:

```bash
# Generate using a built-in preset
process-lab generate-config --preset web_standard -o webserver-config.yml

# Generate with specific flags
process-lab generate-config --sample-rate 90 --filter-type aggressive -o high-filter-config.yml
```

### C. Estimate Cost

Predict the ingest cost for a generated configuration file:

```bash
# Estimate cost for a specific YAML file (requires API Key)
process-lab estimate-cost --yaml webserver-config.yml --price-per-gb 0.30
```

### D. Lint Configuration

Check a configuration file for potential risks:

Check a configuration file for potential risks:

```bash
# Lint a specific YAML file (uses NRDB if API Key provided)
process-lab lint --yaml high-filter-config.yml

# Generate a SARIF report for CI/CD integration
process-lab lint --yaml high-filter-config.yml --sarif report.sarif

### E. Get Recommendations
```

### E. Get Recommendations

Analyze your NRDB data to get suggested configurations:

```bash
# Get recommendations based on the last 7 days of data (requires API Key)
process-lab recommend --window 7d

# Get recommendations and save the best one to a file
process-lab recommend --window 7d --output recommended-config.yml

### F. Generate Rollout Artifacts
```

### F. Generate Rollout Artifacts

Prepare for deployment:

```bash
# Generate Ansible playbook and inventory
process-lab rollout --yaml recommended-config.yml --mode ansible -o ./deploy-artifacts

# Generate a deployment shell script
process-lab rollout --yaml recommended-config.yml --mode script -o ./deploy-artifacts

# Just print example commands
process-lab rollout --yaml recommended-config.yml --mode print

### G. Validate Configuration (Not Fully Implemented)

The `validate` command is included for completeness but is not fully implemented in the current version.

```bash
# Validate configuration (NOT IMPLEMENTED)
process-lab validate --yaml high-filter-config.yml
```

It is intended to compare predicted costs and coverage against actual NRDB data after deployment. For now, use the NRQL queries in `nrdb_analysis/README.md` for manual validation.

### H. (Optional) Local Testing with Docker
```

## 4. (Optional) Local Testing with Docker

The `compose/` directory contains a Docker Compose setup for manually testing generated configurations. The `process-lab` CLI does not manage this environment directly.

```bash
# 1. Generate a configuration file (use -o to avoid overwriting the default)
process-lab generate-config --sample-rate 60 --filter-type standard -o ./test-config.yml

# 2. Copy the generated config to the expected location for Docker Compose
#    (The compose file expects it at config/newrelic-infra.yml)
cp ./test-config.yml config/newrelic-infra.yml

# 3. Start the Docker environment (ensure .env has NEW_RELIC_LICENSE_KEY)
docker compose -f compose/docker-compose.yml up -d

# 4. Let it run for a while (e.g., 15 minutes) to send data...

# 5. (Optional) Manually validate using NRQL queries
#    See nrdb_analysis/README.md for useful queries.

# 6. Stop the Docker environment
docker compose -f compose/docker-compose.yml down

# 7. Clean up volumes if desired
# docker compose -f compose/docker-compose.yml down -v
```

## Further Reading

*   [FAQ](docs/faq.md)
*   [Technical Specification](docs/technical-specification.md)

Use `process-lab <command> --help` for details on specific commands.