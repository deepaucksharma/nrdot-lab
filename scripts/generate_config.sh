#!/bin/bash
# Configuration file generator script
# Usage: ./generate_config.sh [filter_type] [sample_rate] [collect_cmdline]
# Example: ./generate_config.sh aggressive 60 false

# Set defaults
FILTER_TYPE="${1:-standard}"
SAMPLE_RATE="${2:-60}"
COLLECT_CMDLINE="${3:-false}"
TEMPLATE_FILE="../config/newrelic-infra-template.yml"
FILTER_DEFS="../config/filter-definitions.yml"
OUTPUT_DIR="../config"

# Validate filter type
valid_types=("standard" "aggressive" "targeted" "none")
if [[ ! " ${valid_types[*]} " =~ " ${FILTER_TYPE} " ]]; then
    echo "Error: Invalid filter type. Choose from: ${valid_types[*]}"
    exit 1
fi

# Extract filter configuration
if [ "$FILTER_TYPE" == "none" ]; then
    FILTER_CONFIG="# No process filtering"
else
    # Using sed to extract the filter configuration from filter-definitions.yml
    start_line=$(grep -n "^$FILTER_TYPE:" "$FILTER_DEFS" | cut -d: -f1)
    
    if [ -z "$start_line" ]; then
        echo "Error: Could not find filter type $FILTER_TYPE in $FILTER_DEFS"
        exit 1
    fi
    
    # Extract configuration indented under the filter type
    next_type_line=$(tail -n +$((start_line+1)) "$FILTER_DEFS" | grep -n "^[a-z]*:" | head -1 | cut -d: -f1)
    
    if [ -z "$next_type_line" ]; then
        # If no next type, extract till end of file
        FILTER_CONFIG=$(tail -n +$((start_line+1)) "$FILTER_DEFS")
    else
        # Extract until next type
        FILTER_CONFIG=$(tail -n +$((start_line+1)) "$FILTER_DEFS" | head -n $((next_type_line-1)))
    fi
fi

# Generate output file name
OUTPUT_FILE="$OUTPUT_DIR/newrelic-infra-$FILTER_TYPE.yml"

# Create the output file using the template
cat "$TEMPLATE_FILE" | 
    sed "s/\${SAMPLE_RATE:-60}/$SAMPLE_RATE/g" |
    sed "s/\${COLLECT_CMDLINE:-false}/$COLLECT_CMDLINE/g" |
    sed "s/\${FILTER_CONFIG}/$FILTER_CONFIG/g" > "$OUTPUT_FILE"

echo "Generated $OUTPUT_FILE with $FILTER_TYPE filters, sample rate: $SAMPLE_RATE, collect_cmdline: $COLLECT_CMDLINE"
