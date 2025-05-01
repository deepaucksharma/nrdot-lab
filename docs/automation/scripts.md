# Automation Scripts Reference

This page documents the automation scripts available in the ProcessSample Optimization Lab, explaining their purpose, usage, and how to customize them for your needs.

## Available Scripts

The lab includes several scripts in the `scripts/` directory to automate common tasks:

| Script | Purpose |
|--------|---------|
| `validate_ingest.sh` | Check ProcessSample ingest volume |
| `validate_ingest_windows.bat` | Windows version of the validation script |
| `validate_ingest_nojq.sh` | Validation script that doesn't require jq |
| `validate_simple.sh` | Simplified validation with minimal dependencies |
| `ci_smoke.sh` | Run CI smoke tests |
| `run_scenarios.sh` | Run multiple scenarios and compare results |
| `generate_nrdb_report.sh` | Generate detailed NRQL-based reports |
| `generate_visualization.py` | Create visualizations of results |

## Core Validation Scripts

### validate_ingest.sh

This script queries the New Relic API to estimate the volume of ProcessSample data being ingested.

**Usage:**
```bash
./scripts/validate_ingest.sh [options]
```

**Options:**
- `-v` or `--verbose`: Show detailed output
- `-h` or `--help`: Show help information
- `-d` or `--days`: Number of days to analyze (default: 1)

**Example:**
```bash
./scripts/validate_ingest.sh --verbose --days 7
```

**How it works:**

1. The script queries the New Relic GraphQL API using your API key and account ID
2. It runs a NRQL query to estimate the volume of ProcessSample events
3. The results are formatted and displayed, showing GB per day

**Customization:**

You can modify the script to change the NRQL query or add additional queries:

```bash
# Edit this line to change the NRQL query
NRQL_QUERY="SELECT bytecountestimate()/1e9 as 'GB' FROM ProcessSample SINCE ${DAYS} days ago"
```

### validate_ingest_windows.bat

A Windows batch file version of the validation script.

**Usage:**
```cmd
scripts\validate_ingest_windows.bat
```

**Requirements:**
- curl for Windows
- Windows PowerShell

## Scenario Testing Scripts

### run_scenarios.sh

This script automates running multiple lab scenarios and collecting metrics for comparison.

**Usage:**
```bash
./scripts/run_scenarios.sh [duration_minutes]
```

**Example:**
```bash
./scripts/run_scenarios.sh 60
```

**How it works:**

1. The script runs each configured scenario for the specified duration
2. For each scenario, it:
   - Configures the environment variables and compose files
   - Starts the lab with the specific configuration
   - Waits for the specified duration
   - Runs validation to collect metrics
   - Shuts down the lab and saves results
3. After all scenarios complete, it generates a comparison report

**Available Scenarios:**

- **Baseline**: Default configuration (20s sample rate)
- **Standard**: Optimized configuration (60s sample rate with filtering)
- **Minimal**: Minimal mounts configuration
- **Docker Stats**: Configuration with Docker metrics enabled

**Customization:**

You can modify the script to add or remove scenarios:

```bash
# Add a custom scenario
run_scenario "custom" "docker-compose.yml:overrides/my-custom.yml" 
```

## Reporting Scripts

### generate_nrdb_report.sh

This script generates detailed reports based on NRQL queries.

**Usage:**
```bash
./scripts/generate_nrdb_report.sh [output_dir]
```

**Example:**
```bash
./scripts/generate_nrdb_report.sh ./results/report_$(date +%Y%m%d)
```

**How it works:**

1. The script runs a series of NRQL queries against your New Relic account
2. Each query focuses on a different aspect of ProcessSample data
3. The results are saved as markdown files in the output directory

**Queries Include:**

- ProcessSample volume by process
- CPU and memory usage by process
- Process count over time
- Event rate analysis

**Customization:**

You can add custom queries by editing the script:

```bash
# Add a custom query to the report
generate_query_report "Custom Analysis" "SELECT ... FROM ProcessSample ..." "custom-analysis.md"
```

### generate_visualization.py

This Python script creates visualizations of the lab results.

**Usage:**
```bash
python scripts/generate_visualization.py [results_dir] [output_dir]
```

**Example:**
```bash
python scripts/generate_visualization.py ./results ./results/visualizations
```

**Requirements:**
- Python 3.6+
- matplotlib
- pandas

**How it works:**

1. The script reads result files from the specified directory
2. It parses the data and creates various charts:
   - Bar charts comparing different scenarios
   - Line charts showing trends over time
   - Pie charts showing distribution by process
3. The visualizations are saved as PNG files in the output directory
4. A markdown report with embedded visualizations is generated

**Customization:**

You can customize the visualizations by editing the script:

```python
# Change chart style
plt.style.use('seaborn-darkgrid')

# Add a custom visualization
def create_custom_chart(data):
    # Your custom chart code here
    pass
```

## CI Scripts

### ci_smoke.sh

This script runs a smoke test for continuous integration environments.

**Usage:**
```bash
./scripts/ci_smoke.sh
```

**How it works:**

1. The script sets up a minimal lab environment
2. It starts the lab with default configuration
3. It waits for a short period for metrics to be generated
4. It runs basic validation to ensure data is flowing
5. It checks for any errors in the logs
6. It returns a success or failure code

**CI Integration:**

This script is designed to be run in GitHub Actions or other CI environments:

```yaml
# Example GitHub Actions step
- name: Run smoke test
  run: |
    ./scripts/ci_smoke.sh
  env:
    NEW_RELIC_LICENSE_KEY: ${{ secrets.NEW_RELIC_LICENSE_KEY }}
    NEW_RELIC_API_KEY: ${{ secrets.NEW_RELIC_API_KEY }}
    NR_ACCOUNT_ID: ${{ secrets.NR_ACCOUNT_ID }}
```

## Creating Custom Scripts

You can create your own automation scripts by:

1. Creating a new script file in the `scripts/` directory
2. Making it executable: `chmod +x scripts/my_script.sh`
3. Adding documentation for your script in this file

**Example Template:**

```bash
#!/bin/bash
# my_custom_script.sh - Description of what your script does

# Default values
DURATION=30
CONFIG="docker-compose.yml"

# Parse arguments
while [[ $# -gt 0 ]]; do
  case $1 in
    --duration|-d)
      DURATION="$2"
      shift 2
      ;;
    --help|-h)
      echo "Usage: $0 [--duration MINUTES] [--help]"
      exit 0
      ;;
    *)
      echo "Unknown argument: $1"
      exit 1
      ;;
  esac
done

# Script logic
echo "Running custom script with duration: $DURATION minutes"
# Your custom logic here

# Exit with success
exit 0
```

## Troubleshooting Scripts

If you encounter issues with the scripts:

1. **Permission Errors**: Ensure scripts are executable
   ```bash
   chmod +x scripts/*.sh
   ```

2. **API Key Issues**: Verify your API key and account ID are correct in the `.env` file
   ```bash
   grep NEW_RELIC_API_KEY .env
   grep NR_ACCOUNT_ID .env
   ```

3. **JQ Not Found**: Install jq or use the nojq variant
   ```bash
   # Ubuntu/Debian
   apt-get install jq
   
   # macOS
   brew install jq
   
   # Use nojq variant
   ./scripts/validate_ingest_nojq.sh
   ```

4. **Windows Line Endings**: If running on Linux after editing on Windows
   ```bash
   # Fix line endings
   sed -i 's/\r$//' scripts/*.sh
   ```