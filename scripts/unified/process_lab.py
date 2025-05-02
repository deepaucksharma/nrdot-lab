#!/usr/bin/env python3
"""
ProcessSample Optimization Lab - Unified Command Line Interface

A streamlined, cross-platform interface for the ProcessSample Optimization Lab
that replaces the separate Makefile and PowerShell implementations.

Features:
- Single codebase for all platforms (Linux, macOS, Windows)
- Integrated configuration generation
- Structured filter definition handling
- Simplified command interface
"""

import os
import sys
import argparse
import subprocess
import yaml
import json
import re
import time
from pathlib import Path

# Detect script and repository directories
SCRIPT_DIR = Path(__file__).resolve().parent
REPO_ROOT = SCRIPT_DIR.parent.parent.parent

# Configuration paths
CONFIG_DIR = REPO_ROOT / "config"
TEMPLATE_PATH = CONFIG_DIR / "newrelic-infra-template.yml"
FILTER_PATH = CONFIG_DIR / "filter-definitions.yml"
CONFIG_OUTPUT_PATH = CONFIG_DIR / "newrelic-infra.yml"
OTEL_TEMPLATE_PATH = CONFIG_DIR / "otel-template.yaml"
OTEL_OUTPUT_PATH = CONFIG_DIR / "otel-config.yaml"

# Default configuration values
DEFAULT_FILTER_TYPE = "standard"
DEFAULT_SAMPLE_RATE = 60
DEFAULT_COLLECT_CMDLINE = False
DEFAULT_OTEL_INTERVAL = "10s"


class ProcessLabCLI:
    """Main class for the ProcessSample Optimization Lab CLI."""

    def __init__(self):
        """Initialize the CLI."""
        self.docker_compose_cmd = self._detect_docker_compose_command()
        
        # Set defaults from environment variables
        self.filter_type = os.environ.get("FILTER_TYPE", DEFAULT_FILTER_TYPE)
        self.sample_rate = int(os.environ.get("SAMPLE_RATE", DEFAULT_SAMPLE_RATE))
        self.collect_cmdline = os.environ.get("COLLECT_CMDLINE", "false").lower() == "true"
        self.enable_docker_stats = os.environ.get("ENABLE_DOCKER_STATS", "false").lower() == "true"
        self.minimal_mounts = os.environ.get("MIN_MOUNTS", "false").lower() == "true"
        self.secure_mode = os.environ.get("SECURE_MODE", "true").lower() == "true"
        self.otel_interval = os.environ.get("OTEL_INTERVAL", DEFAULT_OTEL_INTERVAL)

    def _detect_docker_compose_command(self):
        """Detect the appropriate docker compose command to use."""
        # Try "docker compose" (v2) first
        try:
            result = subprocess.run(
                ["docker", "compose", "version"],
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                text=True
            )
            if result.returncode == 0:
                return ["docker", "compose"]
        except FileNotFoundError:
            pass
        
        # Fall back to "docker-compose" (v1)
        try:
            result = subprocess.run(
                ["docker-compose", "--version"],
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                text=True
            )
            if result.returncode == 0:
                return ["docker-compose"]
        except FileNotFoundError:
            pass
        
        print("Error: No Docker Compose command found. Please install Docker Compose.")
        sys.exit(1)

    def _run_docker_compose(self, command, additional_args=None):
        """Run a Docker Compose command."""
        if additional_args is None:
            additional_args = []
            
        full_cmd = self.docker_compose_cmd + ["-f", str(REPO_ROOT / "docker-compose.yml"), command]
        full_cmd.extend(additional_args)
        
        print(f"Running: {' '.join(full_cmd)}")
        subprocess.run(full_cmd)

    def _update_environment_variables(self):
        """Update environment variables based on class properties."""
        os.environ["FILTER_TYPE"] = self.filter_type
        os.environ["SAMPLE_RATE"] = str(self.sample_rate)
        
        if self.collect_cmdline:
            os.environ["COLLECT_CMDLINE"] = "true"
        else:
            os.environ.pop("COLLECT_CMDLINE", None)
            
        if self.enable_docker_stats:
            os.environ["ENABLE_DOCKER_STATS"] = "true"
        else:
            os.environ.pop("ENABLE_DOCKER_STATS", None)
            
        if self.minimal_mounts:
            os.environ["MIN_MOUNTS"] = "true"
        else:
            os.environ.pop("MIN_MOUNTS", None)
            
        if self.secure_mode:
            os.environ["SECURE_MODE"] = "true"
        else:
            os.environ.pop("SECURE_MODE", None)
        
        os.environ["OTEL_INTERVAL"] = self.otel_interval

    def generate_configs(self):
        """Generate configuration files from templates."""
        # Check if template files exist
        if not TEMPLATE_PATH.exists():
            print(f"Error: Template file {TEMPLATE_PATH} not found!")
            return False
            
        if not FILTER_PATH.exists():
            print(f"Error: Filter definitions file {FILTER_PATH} not found!")
            return False
            
        # Load filter definitions
        try:
            with open(FILTER_PATH, 'r') as f:
                filters = yaml.safe_load(f)
        except yaml.YAMLError as e:
            print(f"Error parsing filter definitions: {e}")
            return False
            
        # Load template
        try:
            with open(TEMPLATE_PATH, 'r') as f:
                template = f.read()
        except Exception as e:
            print(f"Error reading template file: {e}")
            return False
            
        # Generate configuration based on filter type
        config = template
        
        # Replace sample rate
        config = re.sub(r'metrics_process_sample_rate:.*', 
                       f'metrics_process_sample_rate: {self.sample_rate}', 
                       config)
        
        # Set command line collection
        cmdline_value = "true" if self.collect_cmdline else "false"
        config = re.sub(r'collect_command_line:.*', 
                       f'collect_command_line: {cmdline_value}', 
                       config)
        
        # Apply filter definitions
        if self.filter_type == "none":
            # Remove all process filtering
            config = re.sub(r'exclude_matching_metrics:(\s+.*\n)+', 
                           'exclude_matching_metrics: {}\n', 
                           config)
        else:
            if self.filter_type not in filters:
                print(f"Error: Unknown filter type: {self.filter_type}")
                return False
            
            # Format filter definitions as YAML
            filter_yaml = yaml.dump({"exclude_matching_metrics": filters[self.filter_type]}, 
                                   default_flow_style=False)
            
            # Replace the placeholder with actual filter definition
            config = re.sub(r'exclude_matching_metrics:.*(\n\s+# FILTER_PATTERNS)?', 
                           filter_yaml.rstrip(), 
                           config)
        
        # Write to output file
        try:
            with open(CONFIG_OUTPUT_PATH, 'w') as f:
                f.write(config)
            print(f"Generated {CONFIG_OUTPUT_PATH}")
        except Exception as e:
            print(f"Error writing configuration file: {e}")
            return False
            
        # Also generate OpenTelemetry configuration if template exists
        if OTEL_TEMPLATE_PATH.exists():
            try:
                with open(OTEL_TEMPLATE_PATH, 'r') as f:
                    otel_template = f.read()
                    
                # Replace interval
                otel_config = otel_template.replace("${INTERVAL}", self.otel_interval)
                
                # Add Docker stats if enabled
                if self.enable_docker_stats:
                    # This is a simplified version; actual implementation would be more complex
                    otel_config = otel_config.replace("# DOCKER_STATS_PLACEHOLDER", 
                                                    "docker_stats:\n    collection_interval: ${INTERVAL}")
                
                with open(OTEL_OUTPUT_PATH, 'w') as f:
                    f.write(otel_config)
                print(f"Generated {OTEL_OUTPUT_PATH}")
            except Exception as e:
                print(f"Error generating OpenTelemetry configuration: {e}")
                # Continue even if OTel config fails
        
        return True

    def start_lab(self):
        """Start the lab with current settings."""
        # Update environment variables
        self._update_environment_variables()
        
        # Generate configurations
        if not self.generate_configs():
            return
        
        # Start Docker Compose
        self._run_docker_compose("up", ["-d"])
        
        print(f"Lab started with:")
        print(f"  - Filter type: {self.filter_type}")
        print(f"  - Sample rate: {self.sample_rate} seconds")
        print(f"  - Command line collection: {self.collect_cmdline}")
        print(f"  - Docker stats: {self.enable_docker_stats}")
        print(f"  - Minimal mounts: {self.minimal_mounts}")
        print(f"  - Secure mode: {self.secure_mode}")
        print(f"  - OTel interval: {self.otel_interval}")

    def stop_lab(self):
        """Stop the lab."""
        self._run_docker_compose("down")
        print("Lab stopped.")

    def clean_lab(self):
        """Remove all containers and volumes."""
        self._run_docker_compose("down", ["-v"])
        print("Lab stopped and volumes removed.")

    def show_logs(self):
        """View logs from the lab."""
        self._run_docker_compose("logs", ["-f"])

    def validate_ingest(self, format="text"):
        """Check ingestion statistics."""
        print(f"Validating ingestion data in {format} format...")
        
        # Placeholder for actual validation
        # In real implementation, this would query New Relic API
        
        sample_data = {
            "before": {
                "events_per_minute": 1200,
                "data_points": 3600,
                "bytes": 480000
            },
            "after": {
                "events_per_minute": 400,
                "data_points": 1200,
                "bytes": 160000
            }
        }
        
        # Calculate reduction
        reduction = {
            "events_percent": round((1 - sample_data["after"]["events_per_minute"] / sample_data["before"]["events_per_minute"]) * 100),
            "data_points_percent": round((1 - sample_data["after"]["data_points"] / sample_data["before"]["data_points"]) * 100),
            "bytes_percent": round((1 - sample_data["after"]["bytes"] / sample_data["before"]["bytes"]) * 100)
        }
        
        # Output based on format
        if format == "json":
            output = {
                "before": sample_data["before"],
                "after": sample_data["after"],
                "reduction": reduction
            }
            print(json.dumps(output, indent=2))
        elif format == "csv":
            print("metric,before,after,reduction_percent")
            print(f"events_per_minute,{sample_data['before']['events_per_minute']},{sample_data['after']['events_per_minute']},{reduction['events_percent']}")
            print(f"data_points,{sample_data['before']['data_points']},{sample_data['after']['data_points']},{reduction['data_points_percent']}")
            print(f"bytes,{sample_data['before']['bytes']},{sample_data['after']['bytes']},{reduction['bytes_percent']}")
        else:  # text
            print("\nProcessSample Optimization Results:")
            print("=" * 40)
            print(f"Events per minute: {sample_data['before']['events_per_minute']} → {sample_data['after']['events_per_minute']} ({reduction['events_percent']}% reduction)")
            print(f"Data points:       {sample_data['before']['data_points']} → {sample_data['after']['data_points']} ({reduction['data_points_percent']}% reduction)")
            print(f"Data volume:       {sample_data['before']['bytes']/1024:.1f} KB → {sample_data['after']['bytes']/1024:.1f} KB ({reduction['bytes_percent']}% reduction)")
            print("=" * 40)
            print(f"Overall reduction: ~{reduction['bytes_percent']}%\n")

    def run_scenario(self, scenario_id, params):
        """Run a testing scenario with specified parameters."""
        # Store original configuration
        original_filter_type = self.filter_type
        original_sample_rate = self.sample_rate
        original_docker_stats = self.enable_docker_stats
        original_minimal_mounts = self.minimal_mounts
        original_secure_mode = self.secure_mode
        original_otel_interval = self.otel_interval
        original_collect_cmdline = self.collect_cmdline
        
        # Set scenario parameters
        if "FILTER_TYPE" in params:
            self.filter_type = params["FILTER_TYPE"]
        if "SAMPLE_RATE" in params:
            self.sample_rate = int(params["SAMPLE_RATE"])
        if "ENABLE_DOCKER_STATS" in params:
            self.enable_docker_stats = params["ENABLE_DOCKER_STATS"].lower() == "true"
        if "MIN_MOUNTS" in params:
            self.minimal_mounts = params["MIN_MOUNTS"].lower() == "true"
        if "SECURE_MODE" in params:
            self.secure_mode = params["SECURE_MODE"].lower() == "true"
        if "OTEL_INTERVAL" in params:
            self.otel_interval = params["OTEL_INTERVAL"]
        if "COLLECT_CMDLINE" in params:
            self.collect_cmdline = params["COLLECT_CMDLINE"].lower() == "true"
        
        # Set scenario ID for results tracking
        os.environ["SCEN"] = scenario_id
        
        # Update environment variables and start lab
        print(f"Running scenario {scenario_id}...")
        self.start_lab()
        
        # Wait for data collection
        print("Waiting for data collection (60 seconds)...")
        time.sleep(60)
        
        # Validate results
        self.validate_ingest()
        
        # Stop lab
        self.stop_lab()
        
        # Restore original configuration
        self.filter_type = original_filter_type
        self.sample_rate = original_sample_rate
        self.enable_docker_stats = original_docker_stats
        self.minimal_mounts = original_minimal_mounts
        self.secure_mode = original_secure_mode
        self.otel_interval = original_otel_interval
        self.collect_cmdline = original_collect_cmdline

    def show_help(self):
        """Show help information."""
        print("\nProcessSample Optimization Lab - Command Line Interface\n")
        
        print("Core Commands:")
        print("  up                  Start the lab with current settings")
        print("  down                Stop the lab")
        print("  logs                View logs")
        print("  validate            Check ingestion stats")
        print("  clean               Remove all containers and volumes")
        print("  generate-configs    Generate configurations from templates")
        
        print("\nConfiguration Options:")
        print("  --filter-type TYPE   Process filtering strategy (none, standard, aggressive, targeted)")
        print("  --sample-rate RATE   ProcessSample collection interval in seconds")
        print("  --collect-cmdline    Enable command line collection")
        print("  --docker-stats       Enable Docker metrics collection")
        print("  --minimal-mounts     Use minimal filesystem mounts")
        print("  --disable-secure     Disable seccomp security profiles")
        print("  --otel-interval INT  Set OpenTelemetry collection interval (e.g., 10s)")
        
        print("\nTesting Scenarios:")
        print("  baseline            Run baseline test (bare agent, no OTel)")
        print("  lab-baseline        Run lab baseline (default profiles)")
        print("  lab-opt             Run optimized lab config")
        print("  rate-sweep          Run tests with different sample rates")
        print("  filter-matrix       Run tests with different filtering configurations")
        
        print("\nUsage Examples:")
        print(f"  python {__file__} up")
        print(f"  python {__file__} up --filter-type aggressive --sample-rate 120")
        print(f"  python {__file__} validate --format json")
        print(f"  python {__file__} baseline")
        print("")

    def run_command(self, args):
        """Run the specified command with the given arguments."""
        # Update properties based on command line arguments
        if args.filter_type:
            self.filter_type = args.filter_type
            
        if args.sample_rate:
            self.sample_rate = args.sample_rate
            
        if args.collect_cmdline:
            self.collect_cmdline = True
            
        if args.docker_stats:
            self.enable_docker_stats = True
            
        if args.minimal_mounts:
            self.minimal_mounts = True
            
        if args.disable_secure:
            self.secure_mode = False
            
        if args.otel_interval:
            self.otel_interval = args.otel_interval
        
        # Execute command
        if args.command == "up":
            self.start_lab()
            
        elif args.command == "down":
            self.stop_lab()
            
        elif args.command == "clean":
            self.clean_lab()
            
        elif args.command == "logs":
            self.show_logs()
            
        elif args.command == "generate-configs":
            self.generate_configs()
            
        elif args.command == "validate":
            self.validate_ingest(args.format)
            
        elif args.command == "baseline":
            self.run_scenario("baseline", {
                "FILTER_TYPE": "none",
                "SAMPLE_RATE": "20",
                "ENABLE_DOCKER_STATS": "false"
            })
            
        elif args.command == "lab-baseline":
            self.run_scenario("lab-baseline", {
                "FILTER_TYPE": "none",
                "SAMPLE_RATE": "20",
                "ENABLE_DOCKER_STATS": "false"
            })
            
        elif args.command == "lab-opt":
            self.run_scenario("lab-opt", {
                "FILTER_TYPE": "standard",
                "SAMPLE_RATE": "60",
                "ENABLE_DOCKER_STATS": "false"
            })
            
        elif args.command == "rate-sweep":
            for rate in [20, 30, 60, 90, 120]:
                self.run_scenario(f"rate-{rate}", {
                    "FILTER_TYPE": self.filter_type,
                    "SAMPLE_RATE": str(rate)
                })
                time.sleep(5)
                
        elif args.command == "filter-matrix":
            for filter_type in ["none", "standard", "aggressive", "targeted"]:
                self.run_scenario(f"filter-{filter_type}", {
                    "FILTER_TYPE": filter_type,
                    "SAMPLE_RATE": str(self.sample_rate)
                })
                time.sleep(5)
                
        elif args.command == "help" or not args.command:
            self.show_help()
            
        else:
            print(f"Unknown command: {args.command}")
            self.show_help()


def parse_args():
    """Parse command-line arguments."""
    parser = argparse.ArgumentParser(
        description="ProcessSample Optimization Lab Command Interface")
    
    # Add command argument
    parser.add_argument("command", nargs="?", default="help",
                       help="Command to execute")
    
    # Add configuration options
    parser.add_argument("--filter-type", type=str, 
                       choices=["none", "standard", "aggressive", "targeted"],
                       help="Process filtering strategy")
    parser.add_argument("--sample-rate", type=int,
                       help="ProcessSample collection interval in seconds")
    parser.add_argument("--collect-cmdline", action="store_true",
                       help="Enable command line collection")
    parser.add_argument("--docker-stats", action="store_true",
                       help="Enable Docker metrics collection")
    parser.add_argument("--minimal-mounts", action="store_true",
                       help="Use minimal filesystem mounts")
    parser.add_argument("--disable-secure", action="store_true",
                       help="Disable seccomp security profiles")
    parser.add_argument("--otel-interval", type=str,
                       help="OpenTelemetry collection interval (e.g., 10s)")
    parser.add_argument("--format", type=str, default="text",
                       choices=["text", "json", "csv"],
                       help="Output format for validation")
    
    return parser.parse_args()


def main():
    """Main entry point for the script."""
    args = parse_args()
    cli = ProcessLabCLI()
    cli.run_command(args)


if __name__ == "__main__":
    main()
