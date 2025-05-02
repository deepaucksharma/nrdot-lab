#!/bin/bash
# Verification script to ensure changes work as expected

echo "=== New Relic ProcessSample Optimization Lab Change Verification ==="
echo "This script will verify the changes made to streamline the project."
echo

# Check that key files exist
echo "Checking for key files..."
if [ -f "config/newrelic-infra-template.yml" ]; then
  echo "✅ Configuration template exists"
else
  echo "❌ Configuration template missing"
fi

if [ -f "config/filter-definitions.yml" ]; then
  echo "✅ Filter definitions exist"
else
  echo "❌ Filter definitions missing"
fi

if [ -f "docker-compose.unified.yml" ]; then
  echo "✅ Unified Docker Compose file exists"
else
  echo "❌ Unified Docker Compose file missing"
fi

if [ -f "scripts/validate.sh" ]; then
  echo "✅ Unified validation script exists"
else
  echo "❌ Unified validation script missing"
fi

if [ -f "scripts/visualize.py" ]; then
  echo "✅ Unified visualization script exists"
else
  echo "❌ Unified visualization script missing"
fi

echo
echo "Testing configuration generation..."
# Test the standard configuration generation
if [ -f "scripts/generate_config.sh" ]; then
  echo "Generating standard configuration..."
  chmod +x scripts/generate_config.sh
  scripts/generate_config.sh standard 60 false
  
  if [ -f "config/newrelic-infra-standard.yml" ]; then
    echo "✅ Standard configuration generated successfully"
    echo "Configuration contents:"
    echo "---"
    cat config/newrelic-infra-standard.yml
    echo "---"
  else
    echo "❌ Failed to generate standard configuration"
  fi
else
  echo "❌ Configuration generator script missing"
fi

echo
echo "All verification tests completed."
