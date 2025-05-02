#!/bin/bash
#
# Update script for ProcessSample Optimization Lab
# Updates an existing installation to the latest streamlined structure
#

set -e

echo "========================================================"
echo "  ProcessSample Optimization Lab - Update"
echo "========================================================"
echo

# Check if this is a valid installation
if [ ! -d "config" ] || [ ! -f "docker-compose.yml" ]; then
    echo "Error: This doesn't appear to be a valid ProcessSample Lab directory."
    echo "Please run this script from the root of the ProcessSample Lab project."
    exit 1
fi

# Create backup of important files
echo "Creating backup of current configuration..."
BACKUP_DIR="backup_$(date +%Y%m%d_%H%M%S)"
mkdir -p "$BACKUP_DIR"

# Backup important user files
if [ -f ".env" ]; then
    cp .env "$BACKUP_DIR/"
fi

if [ -f "docker-compose.override.yml" ]; then
    cp docker-compose.override.yml "$BACKUP_DIR/"
fi

if [ -f "config/newrelic-infra.yml" ]; then
    cp config/newrelic-infra.yml "$BACKUP_DIR/"
fi

if [ -f "config/otel-config.yaml" ]; then
    cp config/otel-config.yaml "$BACKUP_DIR/"
fi

echo "Backup created in $BACKUP_DIR"

# Ensure the lab is stopped
echo "Stopping any running containers..."
docker compose down 2>/dev/null || true

# Update scripts directory permissions
echo "Updating script permissions..."
chmod +x scripts/*.sh
chmod +x *.sh

# Generate new configurations
echo "Generating updated configurations..."
./scripts/generate_configs.sh
./scripts/generate_otel_configs.sh

# Verify update
echo "Verifying update..."
if [ ! -f "config/newrelic-infra-standard.yml" ] || [ ! -f "config/otel-config.yaml" ]; then
    echo "Error: Configuration generation failed."
    echo "The update was not successful."
    exit 1
fi

echo
echo "Update completed successfully!"
echo
echo "Changes:"
echo "  - Configuration system is now template-based"
echo "  - Docker Compose has been unified into a single file"
echo "  - Scripts have been streamlined and improved"
echo "  - Cross-platform support has been added"
echo
echo "Your previous configuration has been backed up to $BACKUP_DIR"
echo
echo "Next steps:"
echo "  1. Run 'make up' to start the lab with the updated configuration"
echo "  2. Wait 5-10 minutes for data collection"
echo "  3. Run 'make validate' to check the results"
echo
echo "For more options, run 'make help'"
echo
