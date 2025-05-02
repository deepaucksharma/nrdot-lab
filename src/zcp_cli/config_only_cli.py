"""
Configuration-only CLI for ZCP.

This module provides a minimalist CLI focused exclusively on:
1. Loading presets
2. Rendering templates
3. Estimating costs

No linting, rollout, or validation functionality is included.
"""

import os
import sys
import logging
from typing import Optional
import click

# Configure basic logging
logging.basicConfig(level=logging.INFO, 
                   format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger("zcp")

@click.group()
@click.version_option(version="0.1.0")
def cli():
    """Zero Config Process (ZCP) - Configuration Only CLI"""
    pass

@cli.group()
def preset():
    """Manage presets."""
    pass

@preset.command(name="list")
def list_presets():
    """List available presets."""
    from zcp_preset.loader import PresetLoader
    
    loader = PresetLoader()
    presets = loader.list()
    
    if not presets:
        click.echo("No presets found")
        return
    
    click.echo(f"Found {len(presets)} presets:")
    for preset_id in presets:
        try:
            p = loader.load(preset_id)
            click.echo(f"  {preset_id} (sha256: {p.sha256[:8]}...)")
        except Exception as e:
            click.echo(f"  {preset_id} (ERROR: {e})")

@preset.command(name="show")
@click.argument("preset_id")
def show_preset(preset_id: str):
    """Show details of a specific preset."""
    try:
        from zcp_preset.loader import PresetLoader
        
        loader = PresetLoader()
        p = loader.load(preset_id)
        click.echo(p.to_json())
    except FileNotFoundError:
        click.echo(f"Preset not found: {preset_id}", err=True)
        sys.exit(1)
    except Exception as e:
        click.echo(f"Error loading preset: {e}", err=True)
        sys.exit(1)

@cli.command()
@click.option("--preset", "-p", required=True, help="Preset ID to use")
@click.option("--output", "-o", help="Output file for generated configuration")
def generate(preset: str, output: Optional[str]):
    """Generate a configuration from a preset."""
    from zcp_preset.loader import PresetLoader
    
    # Load preset
    try:
        loader = PresetLoader()
        p = loader.load(preset)
        click.echo(f"Loaded preset: {p.id}")
    except Exception as e:
        click.echo(f"Error loading preset: {e}", err=True)
        sys.exit(1)
    
    # Generate configuration
    try:
        # Use simple string template approach
        template_content = """
integrations:
  - name: nri-process-discovery
    config:
      interval: {sample_rate}
      discovery:
        mode: {filter_mode}
        match_patterns:
{match_patterns}
""".format(
            sample_rate=p.default_sample_rate,
            filter_mode=p.filter_mode,
            match_patterns="\n".join([f"          - {pattern}" for pattern in p.tier1_patterns])
        )
    except Exception as e:
        click.echo(f"Error generating configuration: {e}", err=True)
        sys.exit(1)
    
    # Output the configuration
    if output:
        try:
            with open(output, "w") as f:
                f.write(template_content)
            click.echo(f"Configuration saved to {output}")
        except Exception as e:
            click.echo(f"Error writing configuration: {e}", err=True)
            sys.exit(1)
    else:
        click.echo("\nGenerated configuration:")
        click.echo("-------------------------")
        click.echo(template_content)

@cli.command()
@click.option("--preset", "-p", required=True, help="Preset ID to use")
@click.option("--host-count", "-n", type=int, default=1, help="Number of hosts")
def estimate(preset: str, host_count: int):
    """Estimate data ingest cost for a configuration."""
    from zcp_preset.loader import PresetLoader
    
    # Load preset
    try:
        loader = PresetLoader()
        p = loader.load(preset)
        click.echo(f"Loaded preset: {p.id}")
    except Exception as e:
        click.echo(f"Error loading preset: {e}", err=True)
        sys.exit(1)
    
    # Calculate cost directly
    try:
        # Daily ingest in bytes
        bytes_per_day = (
            host_count *                   # Number of hosts
            p.avg_bytes_per_sample *      # Bytes per sample
            (86400 / p.default_sample_rate) *        # Samples per day
            p.expected_keep_ratio         # Ratio of processes that match filter
        )
        
        # Convert to GiB
        gib_per_day = bytes_per_day / (1024 * 1024 * 1024)
        
        click.echo(f"Estimated data ingest: {gib_per_day:.2f} GiB/day")
        click.echo(f"Based on {host_count} hosts with {p.default_sample_rate}s sampling rate")
    except Exception as e:
        click.echo(f"Error estimating cost: {e}", err=True)
        sys.exit(1)

@cli.command()
@click.option("--preset", "-p", default="java_heavy", help="Preset ID to use")
@click.option("--host-count", "-n", type=int, default=1, help="Number of hosts")
@click.option("--output", "-o", help="Output file for generated configuration")
def wizard(preset: str, host_count: int, output: Optional[str]):
    """
    Run a simplified configuration wizard.
    
    This command guides you through:
    1. Loading a preset
    2. Generating a configuration
    3. Estimating data ingest cost
    """
    from zcp_preset.loader import PresetLoader
    
    # 1. Load preset
    click.echo(f"Loading preset: {preset}")
    try:
        loader = PresetLoader()
        p = loader.load(preset)
        click.echo(f"Loaded preset: {p.id}")
    except Exception as e:
        click.echo(f"Error loading preset: {e}", err=True)
        sys.exit(1)
    
    # 2. Generate configuration
    click.echo("Generating configuration...")
    try:
        template_content = """
integrations:
  - name: nri-process-discovery
    config:
      interval: {sample_rate}
      discovery:
        mode: {filter_mode}
        match_patterns:
{match_patterns}
""".format(
            sample_rate=p.default_sample_rate,
            filter_mode=p.filter_mode,
            match_patterns="\n".join([f"          - {pattern}" for pattern in p.tier1_patterns])
        )
        
        # Calculate checksum
        import hashlib
        checksum = hashlib.sha256(template_content.encode()).hexdigest()
        click.echo(f"Configuration generated (checksum: {checksum[:8]}...)")
    except Exception as e:
        click.echo(f"Error generating configuration: {e}", err=True)
        sys.exit(1)
    
    # 3. Estimate cost
    click.echo("Estimating data ingest cost...")
    try:
        # Daily ingest in bytes
        bytes_per_day = (
            host_count *                   # Number of hosts
            p.avg_bytes_per_sample *      # Bytes per sample
            (86400 / p.default_sample_rate) *        # Samples per day
            p.expected_keep_ratio         # Ratio of processes that match filter
        )
        
        # Convert to GiB
        gib_per_day = bytes_per_day / (1024 * 1024 * 1024)
        
        click.echo(f"Estimated data ingest: {gib_per_day:.2f} GiB/day")
        click.echo(f"Based on {host_count} hosts with {p.default_sample_rate}s sampling rate")
    except Exception as e:
        click.echo(f"Error estimating cost: {e}", err=True)
        sys.exit(1)
    
    # Show or save the generated configuration
    if output:
        try:
            with open(output, "w") as f:
                f.write(template_content)
            click.echo(f"Configuration saved to {output}")
        else:
            click.echo("\nGenerated configuration:")
            click.echo("-------------------------")
            click.echo(template_content)
    
    click.echo("\nWizard completed successfully!")

if __name__ == "__main__":
    cli()
