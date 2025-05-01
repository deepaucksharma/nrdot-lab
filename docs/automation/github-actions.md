# GitHub Actions for ProcessSample Lab

This page documents the GitHub Actions workflows available for automating tests, validations, and documentation for the ProcessSample Optimization Lab.

## Available Workflows

The repository includes several GitHub Actions workflows for different purposes:

| Workflow | File | Purpose | Trigger |
|----------|------|---------|---------|
| [CI Smoke Test](#ci-smoke-test) | `ci.yml` | Basic smoke testing | On push, PR |
| [Documentation](#documentation) | `docs.yml` | Build and deploy docs | On push to docs, manual |
| [Data Experiment](#data-experiment) | `data-experiment.yml` | Custom experiment runner | Manual |
| [Scenario Tests](#scenario-tests) | `scenario-tests.yml` | Comprehensive scenario testing | Weekly, manual |

## CI Smoke Test

The CI workflow runs a basic smoke test to ensure the lab environment starts correctly and passes validation checks.

```yaml
name: CI

on:
  push:
    branches: [ master ]
  pull_request:
    branches: [ master ]

jobs:
  smoke-test:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v3
      
      - name: Set up Docker
        uses: docker/setup-buildx-action@v2
      
      - name: Create dummy .env file
        run: |
          cp .env.example .env
          echo "NEW_RELIC_LICENSE_KEY=0123456789abcdef0123456789abcdef01234567" >> .env
          echo "NR_ACCOUNT_ID=12345678" >> .env
      
      - name: Run smoke test
        run: |
          chmod +x ./scripts/ci_smoke.sh
          chmod +x ./scripts/validate_ingest.sh
          # Fix permissions for the entrypoint.sh in the container
          chmod +x ./load-image/entrypoint.sh
          ./scripts/ci_smoke.sh
```

### How It Works

1. Checks out the repository code
2. Sets up Docker for container operations
3. Creates a dummy .env file with placeholder credentials
4. Runs the `ci_smoke.sh` script which:
   - Starts the containers with default configuration
   - Waits for the environment to stabilize
   - Runs basic validation
   - Shuts down the environment

## Documentation

The Documentation workflow builds and deploys the MkDocs site to GitHub Pages.

```yaml
name: Documentation
on:
  push:
    branches: [master]
    paths:
      - 'docs/**'
      - 'CHANGELOG.md'
      - 'mkdocs.yml'
  # Allow manual trigger
  workflow_dispatch:

jobs:
  build:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v3
        with:
          fetch-depth: 0
      - uses: actions/setup-python@v4
        with: 
          python-version: '3.11'
      - name: Install dependencies
        run: pip install mkdocs-material pymdown-extensions
      - name: Deploy docs
        run: |
          git config --global user.name "GitHub Actions"
          git config --global user.email "actions@github.com"
          mkdocs gh-deploy --force
```

### How It Works

1. Triggered when changes are made to the docs directory, CHANGELOG.md, or mkdocs.yml
2. Can also be triggered manually
3. Checks out the repository with full history
4. Sets up Python and installs MkDocs with the Material theme
5. Configures Git for the commit to gh-pages branch
6. Deploys the documentation to GitHub Pages

## Data Experiment

The Data Experiment workflow allows running longer-duration data collection experiments to compare different optimization strategies.

```yaml
name: Data Experiment

on:
  workflow_dispatch:
    inputs:
      duration_minutes:
        description: 'Duration in minutes to run each scenario'
        required: true
        default: '30'
      run_baseline:
        description: 'Run baseline scenario (20s, no filtering)'
        type: boolean
        default: true
      run_standard:
        description: 'Run standard scenario (60s with filtering)'
        type: boolean
        default: true
      run_minimal_mounts:
        description: 'Run minimal mounts scenario'
        type: boolean
        default: true

jobs:
  run-experiments:
    # ...workflow implementation...
```

### How It Works

1. Triggered manually with configurable inputs
2. Allows selecting which scenarios to run
3. Sets the duration for each scenario
4. Creates a custom script to run the selected scenarios
5. Generates a summary report with results
6. Uploads the results as an artifact for download

## Scenario Tests

The Scenario Tests workflow runs all predefined scenarios and generates comprehensive comparison reports.

```yaml
name: Scenario Tests

on:
  workflow_dispatch:
    inputs:
      duration_minutes:
        description: 'Duration in minutes to run each scenario'
        required: true
        default: '15'
  schedule:
    # Run weekly on Sunday at 1:00 AM UTC
    - cron: '0 1 * * 0'

jobs:
  run-all-scenarios:
    # ...workflow implementation...
```

### How It Works

1. Runs on a weekly schedule and can also be triggered manually
2. Tests all predefined scenarios:
   - Baseline (20s sample rate)
   - Standard (60s sample rate)
   - Filtered (60s with process filtering)
   - Minimal Mounts (restricted filesystem access)
   - Docker Stats (with container metrics)
   - Seccomp Off (for troubleshooting)
   - Full Optimization (combined strategies)
3. Generates a detailed report with comparisons
4. Creates visualizations if the python script is available
5. Updates the documentation with the latest results
6. Uploads all results as artifacts

## Using the Workflows

### Setting Up Secrets

To use these workflows with real New Relic credentials, add the following repository secrets:

1. Go to your repository Settings → Secrets and variables → Actions
2. Add the following secrets:
   - `NEW_RELIC_LICENSE_KEY`: Your New Relic license key
   - `NEW_RELIC_API_KEY`: Your New Relic User API key
   - `NR_ACCOUNT_ID`: Your New Relic account ID

### Running Manually

To run a workflow manually:

1. Go to the "Actions" tab in your GitHub repository
2. Select the workflow you want to run
3. Click "Run workflow"
4. Configure any inputs if prompted
5. Click "Run workflow" to start

### Viewing Results

After a workflow runs:

1. Go to the "Actions" tab
2. Click on the completed workflow run
3. Scroll down to the "Artifacts" section
4. Download the artifacts to view results

For documentation updates, visit your GitHub Pages site after the workflow completes.

## Extending Workflows

You can extend these workflows to fit your specific needs:

### Adding New Scenarios

1. Edit the `scenario-tests.yml` file
2. Add a new scenario to the `run_all_scenarios.sh` script generator section
3. Follow the existing pattern for scenario configuration

### Customizing Test Duration

1. Update the default duration in the workflow input parameters
2. For scheduled runs, modify the hardcoded duration in the workflow

### Adding Custom Metrics

1. Extend the reporting logic in the scripts
2. Add custom validation scripts in the scripts directory
3. Update the workflow to call your custom scripts

## Troubleshooting

### Common Issues

1. **Workflow fails with Docker errors**:
   - Check that the Docker setup is correct
   - Verify file permissions on shell scripts

2. **Missing New Relic data**:
   - Verify the secrets are correctly configured
   - Check that the environment variables are properly passed to containers

3. **Documentation not updating**:
   - Ensure GitHub Pages is enabled in repository settings
   - Check the workflow logs for deployment errors

### Getting Help

If you encounter persistent issues with the workflows:

1. Check the workflow run logs for detailed error messages
2. Open an issue on the GitHub repository
3. Include relevant logs and error messages
