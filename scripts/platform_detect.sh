#!/bin/bash
#
# Platform detection script for ProcessSample Optimization Lab
# Detects the platform and outputs appropriate commands and paths
#

# Platform detection
if [[ "$OSTYPE" == "linux-gnu"* ]]; then
    PLATFORM="linux"
elif [[ "$OSTYPE" == "darwin"* ]]; then
    PLATFORM="macos"
elif [[ "$OSTYPE" == "msys" || "$OSTYPE" == "cygwin" || "$OSTYPE" == "win32" ]]; then
    PLATFORM="windows"
else
    PLATFORM="unknown"
fi

# Docker Compose command detection
if command -v docker compose &> /dev/null; then
    DOCKER_COMPOSE_CMD="docker compose"
elif command -v docker-compose &> /dev/null; then
    DOCKER_COMPOSE_CMD="docker-compose"
else
    echo "Error: Docker Compose not found. Please install Docker and Docker Compose."
    exit 1
fi

# Output platform info
echo "PLATFORM=$PLATFORM"
echo "DOCKER_COMPOSE_CMD=$DOCKER_COMPOSE_CMD"

# Output platform-specific paths
if [[ "$PLATFORM" == "windows" ]]; then
    echo "PATH_SEPARATOR=\\"
    echo "SCRIPT_EXT=.ps1"
else
    echo "PATH_SEPARATOR=/"
    echo "SCRIPT_EXT=.sh"
fi

# Check for potential line ending issues
if [[ "$PLATFORM" == "windows" ]]; then
    # Check for CRLF in scripts that will run in Docker
    if command -v file &> /dev/null; then
        CRLF_FILES=$(find ./load-image -name "*.sh" -exec file {} \; | grep CRLF | wc -l)
        if [[ $CRLF_FILES -gt 0 ]]; then
            echo "WARNING: CRLF_DETECTED=true"
            echo "Some shell scripts have Windows-style line endings (CRLF)."
            echo "This may cause issues in Docker containers."
            echo "Consider converting to Unix-style line endings (LF) using:"
            echo "find ./load-image -name \"*.sh\" -exec dos2unix {} \;"
        else
            echo "CRLF_DETECTED=false"
        fi
    fi
fi

# Exit successfully
exit 0
