#!/usr/bin/env python3
"""
ProcessSample Optimization Lab - Unified Setup Script

This script prepares the environment for the ProcessSample Optimization Lab.
It works consistently across all platforms (Linux, macOS, Windows).
"""

import os
import sys
import subprocess
import shutil
from pathlib import Path

# Detect script directory
SCRIPT_DIR = Path(__file__).resolve().parent

def check_prerequisites():
    """Check if all prerequisites are installed."""
    print("Checking prerequisites...")
    
    # Check Python version
    python_version = sys.version_info
    if python_version.major < 3 or (python_version.major == 3 and python_version.minor < 6):
        print("Error: Python 3.6 or higher is required.")
        return False
    
    # Check Docker
    try:
        result = subprocess.run(
            ["docker", "--version"],
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True
        )
        if result.returncode != 0:
            print("Error: Docker is not installed or not running.")
            return False
        print(f"Found Docker: {result.stdout.strip()}")
    except FileNotFoundError:
        print("Error: Docker is not installed or not in PATH.")
        return False
    
    # Check Docker Compose
    docker_compose_cmd = None
    try:
        result = subprocess.run(
            ["docker", "compose", "version"],
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True
        )
        if result.returncode == 0:
            docker_compose_cmd = ["docker", "compose"]
            print(f"Found Docker Compose v2: {result.stdout.strip()}")
    except FileNotFoundError:
        pass
    
    if not docker_compose_cmd:
        try:
            result = subprocess.run(
                ["docker-compose", "--version"],
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                text=True
            )
            if result.returncode == 0:
                docker_compose_cmd = ["docker-compose"]
                print(f"Found Docker Compose v1: {result.stdout.strip()}")
        except FileNotFoundError:
            print("Error: Docker Compose is not installed or not in PATH.")
            return False
    
    # Check Python dependencies
    try:
        import yaml
        print("Found PyYAML module.")
    except ImportError:
        print("Installing PyYAML...")
        subprocess.run([sys.executable, "-m", "pip", "install", "pyyaml"])
    
    return True

def setup_environment():
    """Set up the environment variables."""
    print("Setting up environment...")
    
    env_example = SCRIPT_DIR / ".env.example"
    env_file = SCRIPT_DIR / ".env"
    
    if not env_example.exists():
        print("Error: .env.example file not found.")
        return False
    
    if env_file.exists():
        print(".env file already exists. Skipping creation.")
    else:
        # Copy .env.example to .env
        shutil.copy(env_example, env_file)
        print("Created .env file from .env.example.")
        print("Please edit .env with your New Relic credentials.")
    
    return True

def setup_configuration_directories():
    """Set up configuration directories."""
    print("Setting up configuration directories...")
    
    # Create directories if they don't exist
    dirs = [
        SCRIPT_DIR / "config",
        SCRIPT_DIR / "results"
    ]
    
    for directory in dirs:
        directory.mkdir(exist_ok=True)
        print(f"Created directory: {directory}")
    
    return True

def generate_initial_configs():
    """Generate initial configuration files."""
    print("Generating initial configuration files...")
    
    # Run the configuration generator
    process_lab_script = SCRIPT_DIR / "scripts" / "unified" / "process_lab.py"
    
    if not process_lab_script.exists():
        print("Error: process_lab.py script not found.")
        return False
    
    try:
        subprocess.run(
            [sys.executable, str(process_lab_script), "generate-configs"],
            check=True
        )
    except subprocess.CalledProcessError as e:
        print(f"Error generating configurations: {e}")
        return False
    
    return True

def main():
    """Main setup function."""
    print("===================================================")
    print("New Relic ProcessSample Optimization Lab Setup")
    print("===================================================")
    
    if not check_prerequisites():
        print("Setup failed: Prerequisites check failed.")
        return 1
    
    if not setup_environment():
        print("Setup failed: Environment setup failed.")
        return 1
    
    if not setup_configuration_directories():
        print("Setup failed: Directory setup failed.")
        return 1
    
    if not generate_initial_configs():
        print("Setup failed: Configuration generation failed.")
        return 1
    
    print("===================================================")
    print("Setup completed successfully!")
    print("\nNext steps:")
    print("1. Edit .env file with your New Relic credentials")
    print("2. Run the lab with: python scripts/unified/process_lab.py up")
    print("3. Check results with: python scripts/unified/process_lab.py validate")
    print("===================================================")
    
    return 0

if __name__ == "__main__":
    sys.exit(main())
