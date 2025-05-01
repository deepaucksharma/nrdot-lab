# GitHub Actions for the ProcessSample Lab

This page documents the GitHub Actions workflows available for automating tests, validations, and documentation for the ProcessSample Optimization Lab.

## Available Workflows

### CI Smoke Test

This workflow runs a basic smoke test to ensure the lab environment starts correctly and passes validation checks.

```yaml
name: CI Smoke Test

on:
  push:
    branches: [ main ]
  pull_request:
    branches: [ main ]

jobs:
  smoke_test:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v3

      - name: Setup environment
        run: |
          cp .env.example .env
          echo "NEW_RELIC_LICENSE_KEY=${{ secrets.NEW_RELIC_LICENSE_KEY }}" >> .env
          echo "NEW_RELIC_API_KEY=${{ secrets.NEW_RELIC_API_KEY }}" >> .env
          echo "NR_ACCOUNT_ID=${{ secrets.NR_ACCOUNT_ID }}" >> .env
          
      - name: Run smoke test
        run: |
          make smoke
```

### Documentation Site

This workflow automatically builds and deploys the documentation site to GitHub Pages whenever changes are pushed to the main branch.

```yaml
name: Documentation

on:
  push:
    branches: [main]
    paths:
      - 'docs/**'
      - 'CHANGELOG.md'
      - 'mkdocs.yml'

jobs:
  deploy_docs:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v3
        with:
          fetch-depth: 0
      
      - uses: actions/setup-python@v4
        with:
          python-version: '3.11'
      
      - name: Install dependencies
        run: |
          pip install mkdocs-material pymdown-extensions
      
      - name: Build and deploy documentation
        run: |
          mkdocs gh-deploy --force
```

### Data Experiment Runner

This workflow allows running longer-duration data collection experiments to compare different optimization strategies.

```yaml
name: Data Experiment

on:
  workflow_dispatch:
    inputs:
      duration_minutes:
        description: 'Duration for each scenario (minutes)'
        required: true
        default: '30'
      run_baseline:
        description: 'Run baseline (unoptimized) scenario'
        required: true
        type: boolean
        default: true
      run_standard:
        description: 'Run standard optimized scenario'
        required: true
        type: boolean
        default: true
      run_minimal:
        description: 'Run minimal mounts scenario'
        required: true
        type: boolean
        default: true
      run_docker_stats:
        description: 'Run docker stats scenario'
        required: true
        type: boolean
        default: false

jobs:
  run_experiments:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v3

      - name: Setup environment
        run: |
          cp .env.example .env
          echo "NEW_RELIC_LICENSE_KEY=${{ secrets.NEW_RELIC_LICENSE_KEY }}" >> .env
          echo "NEW_RELIC_API_KEY=${{ secrets.NEW_RELIC_API_KEY }}" >> .env
          echo "NR_ACCOUNT_ID=${{ secrets.NR_ACCOUNT_ID }}" >> .env
          
      - name: Run experiments
        run: |
          export DURATION_MINUTES=${{ github.event.inputs.duration_minutes }}
          export RUN_BASELINE=${{ github.event.inputs.run_baseline }}
          export RUN_STANDARD=${{ github.event.inputs.run_standard }}
          export RUN_MINIMAL=${{ github.event.inputs.run_minimal }}
          export RUN_DOCKER_STATS=${{ github.event.inputs.run_docker_stats }}
          ./scripts/run_experiment.sh
          
      - name: Upload results
        uses: actions/upload-artifact@v3
        with:
          name: experiment-results
          path: results/
```

## Setting Up GitHub Actions

To use these workflows in your own fork or copy of the lab:

1. **Configure Secrets**: Add the following repository secrets in your GitHub repository settings:
   - `NEW_RELIC_LICENSE_KEY`: Your New Relic license key
   - `NEW_RELIC_API_KEY`: Your New Relic User API key
   - `NR_ACCOUNT_ID`: Your New Relic account ID

2. **Enable GitHub Pages**: In your repository settings, configure GitHub Pages to deploy from the `gh-pages` branch.

3. **Save Workflow Files**: Save each workflow as a YAML file in the `.github/workflows/` directory:
   - `.github/workflows/ci.yml` for the CI Smoke Test
   - `.github/workflows/docs.yml` for the Documentation Site
   - `.github/workflows/experiment.yml` for the Data Experiment Runner

## Using the Workflows

### Running the Data Experiment

1. Navigate to the "Actions" tab in your GitHub repository
2. Select the "Data Experiment" workflow
3. Click "Run workflow"
4. Configure the experiment parameters:
   - Duration for each scenario (in minutes)
   - Which scenarios to run
5. Click "Run workflow" to start the experiment
6. When complete, download the experiment results from the "Artifacts" section

### Triggering Documentation Builds

The documentation workflow runs automatically when changes are pushed to the main branch and they affect the documentation files.

To trigger a manual build:

1. Navigate to the "Actions" tab in your GitHub repository
2. Select the "Documentation" workflow
3. Click "Run workflow"
4. Select the branch to build from
5. Click "Run workflow"

## Viewing Documentation Site

After the documentation workflow runs successfully, your documentation site will be available at:

```
https://<username-or-org>.github.io/<repository-name>/
```

For example, if your GitHub username is "example" and the repository is "process-lab", the site would be at:

```
https://example.github.io/process-lab/
```

## Troubleshooting Workflows

### CI Smoke Test Failures

If the CI smoke test fails:

1. Check the workflow logs for specific error messages
2. Verify that your New Relic credentials are correct in the repository secrets
3. Check for any Docker-related issues in the logs

### Documentation Build Failures

Common issues with documentation builds:

1. **Missing Dependencies**: Ensure the workflow installs all required Python packages
2. **YAML Syntax Errors**: Check for YAML syntax errors in your documentation files
3. **Permission Issues**: Ensure the workflow has permission to write to the gh-pages branch

If you encounter persistent issues, check the GitHub Actions logs for detailed error messages.