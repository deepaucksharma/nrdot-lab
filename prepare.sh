#!/bin/bash
#
# Prepare Script for ProcessSample Optimization Lab
# Sets up the environment and prepares for pushing changes
#

echo "Preparing ProcessSample Optimization Lab for pushing..."
echo "======================================================="
echo ""

# Get script directory
SCRIPT_DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"

# Step 1: Run platform detection
echo "Step 1: Detecting platform and environment..."
"$SCRIPT_DIR/scripts/platform_detect.sh"
echo "Platform detection complete."
echo ""

# Step 2: Fix line endings
echo "Step 2: Fixing line endings in shell scripts..."
"$SCRIPT_DIR/scripts/fix_line_endings.sh"
echo ""

# Step 3: Generate configurations
echo "Step 3: Generating configurations..."
"$SCRIPT_DIR/scripts/generate_configs.sh"
"$SCRIPT_DIR/scripts/generate_otel_configs.sh"
echo "Configuration generation complete."
echo ""

# Step 4: Verify setup
echo "Step 4: Verifying setup..."
if [ -f "$SCRIPT_DIR/scripts/verify_setup.sh" ]; then
    "$SCRIPT_DIR/scripts/verify_setup.sh"
else
    echo "Verification script not found, skipping verification."
fi
echo ""

# Step 5: Instructions for pushing
echo "Step 5: Preparation for pushing to repository..."
echo "To push changes to your repository, run the following Git commands:"
echo ""
echo "git add ."
echo "git commit -m 'Streamline ProcessSample Lab project end-to-end'"
echo "git push origin main"
echo ""
echo "If using a branch:"
echo "git checkout -b streamlined-version"
echo "git add ."
echo "git commit -m 'Streamline ProcessSample Lab project end-to-end'"
echo "git push origin streamlined-version"
echo ""

echo "Preparation complete!"
