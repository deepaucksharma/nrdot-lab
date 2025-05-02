#!/bin/bash
#
# Fix Line Endings Script for ProcessSample Optimization Lab
# Converts Windows-style line endings (CRLF) to Unix-style (LF) in shell scripts
#

echo "Checking line endings in shell scripts..."

# Check if dos2unix is available
if command -v dos2unix &> /dev/null; then
    # Best option - use dos2unix
    echo "Using dos2unix to fix line endings..."
    
    # Find all shell scripts and convert them
    find . -name "*.sh" -type f -exec dos2unix {} \;
    find ./load-image -name "entrypoint*" -type f -exec dos2unix {} \;
    
    echo "Line ending conversion complete."
else
    # Fallback option - use sed
    echo "dos2unix not found, using sed as fallback..."
    
    # Function to check and convert a file
    fix_file() {
        local file="$1"
        if grep -q $'\r' "$file"; then
            echo "  Converting $file to LF line endings"
            sed -i 's/\r$//' "$file"
            return 1
        fi
        return 0
    }
    
    # Find all shell scripts
    script_count=0
    fixed_count=0
    
    while IFS= read -r -d '' file; do
        script_count=$((script_count+1))
        if ! fix_file "$file"; then
            fixed_count=$((fixed_count+1))
        fi
    done < <(find . -name "*.sh" -type f -print0)
    
    # Also check entrypoint scripts that might not have .sh extension
    while IFS= read -r -d '' file; do
        script_count=$((script_count+1))
        if ! fix_file "$file"; then
            fixed_count=$((fixed_count+1))
        fi
    done < <(find ./load-image -name "entrypoint*" -type f -print0)
    
    echo ""
    echo "Line ending conversion complete."
    echo "Checked $script_count script files."
    echo "Fixed $fixed_count files with Windows-style line endings."
    
    if [ "$fixed_count" -gt 0 ]; then
        echo ""
        echo "IMPORTANT: The files have been converted to Unix-style line endings (LF)."
        echo "This will prevent the 'No such file or directory' errors in Docker containers."
    fi
fi

echo ""
echo "Done."
