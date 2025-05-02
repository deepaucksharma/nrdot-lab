#!/bin/bash
#
# Setup script for ProcessSample Optimization Lab
# Initializes the project with all required configurations
#

set -e

echo "========================================================"
echo "  ProcessSample Optimization Lab - Initial Setup"
echo "========================================================"
echo

# Check for Docker
if ! command -v docker &> /dev/null; then
    echo "Error: Docker is not installed or not in PATH."
    echo "Please install Docker before continuing."
    exit 1
fi

# Check Docker Compose
if ! command -v docker compose &> /dev/null; then
    if ! command -v docker-compose &> /dev/null; then
        echo "Error: Docker Compose is not installed or not in PATH."
        echo "Please install Docker Compose before continuing."
        exit 1
    else
        echo "Note: Using legacy docker-compose command."
    fi
fi

# Check for environment file
if [ ! -f .env ]; then
    if [ -f .env.example ]; then
        echo "Creating .env file from example..."
        cp .env.example .env
        echo "Please edit .env with your New Relic license key, API key, and account ID."
    else
        echo "Error: .env.example file not found."
        exit 1
    fi
fi

# Make scripts executable
echo "Making scripts executable..."
chmod +x scripts/*.sh
chmod +x *.sh

# Generate configurations
echo "Generating configurations..."
./scripts/generate_configs.sh
./scripts/generate_otel_configs.sh

# Create necessary directories
echo "Creating directory structure..."
mkdir -p results
mkdir -p results/visualizations

# Verify setup
echo "Verifying setup..."
if [ ! -f "config/newrelic-infra-standard.yml" ]; then
    echo "Error: Configuration generation failed."
    exit 1
fi

if [ ! -f "config/otel-config.yaml" ]; then
    echo "Error: OpenTelemetry configuration generation failed."
    exit 1
fi

echo
echo "Setup completed successfully!"
echo
echo "Next steps:"
echo "  1. Edit .env with your New Relic license key, API key, and account ID"
echo "  2. Run 'make up' to start the lab"
echo "  3. Wait 5-10 minutes for data collection"
echo "  4. Run 'make validate' to check the results"
echo
echo "For more options, run 'make help'"
echo
