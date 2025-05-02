"""
Simplified CLI for ZCP.

This module provides a streamlined CLI with only the essential commands
needed for the core workflow: preset → template → lint → cost → rollout → validate.
"""

import os
import sys
import logging
from typing import List, Optional

import click
import yaml

# Configure basic logging
logging.basicConfig(level=logging.INFO, 
                   format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger("zcp")

@click.group()
@click.version_option(version="0.1.0")
def cli():
    """Zero Config Process (ZCP) - Simplified CLI"""
    pass

@cli.command()
@click.option("--preset", "-p", default="java_heavy", help="Preset ID to use")
@click.option("--host-count", "-n", type=int, default=1, help="Number of hosts")
@click.option("--hosts", help="Comma-separated list of hosts for rollout")
@click.option("--rollout", is_flag=True, help="Perform rollout after configuration")
@click.option("--validate", is_flag=True, help="Validate after rollout")
def wizard(preset: str, host_count: int, hosts: Optional[str], rollout: bool, validate: bool):
    """
    Run the configuration wizard.
    
    This is the main command that guides you through the entire workflow:
    1. Load a preset
    2. Render a configuration template
    3. Lint the configuration
    4. Estimate data ingest cost
    5. Optionally roll out to hosts
    6. Optionally validate the rollout
    """
    from zcp_preset.loader import PresetLoader
    from zcp_cost.simple_cost import estimate_cost, CostRequest
    from zcp_lint.simple_lint import lint_config
    
    # 1. Load preset
    click.echo(f"Loading preset: {preset}")
    try:
        loader = PresetLoader()
        p = loader.load(preset)
        click.echo(f"Loaded preset: {p.id}")
    except Exception as e:
        click.echo(f"Error loading preset: {e}", err=True)
        sys.exit(1)
    
    # 2. Render template (simple string formatting)
    click.echo("Rendering configuration template...")
    try:
        # Use simpler string template approach
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
        click.echo(f"Configuration rendered (checksum: {checksum[:8]}...)")
    except Exception as e:
        click.echo(f"Error rendering template: {e}", err=True)
        sys.exit(1)
    
    # 3. Lint the configuration
    click.echo("Linting configuration...")
    try:
        lint_result = lint_config(template_content)
        if lint_result.has_errors:
            click.echo(f"Linting found {lint_result.error_count} errors:")
            for finding in lint_result.findings:
                if finding.severity == "error":
                    click.echo(f"  ERROR: {finding.message}")
            sys.exit(1)
        elif lint_result.warning_count > 0:
            click.echo(f"Linting found {lint_result.warning_count} warnings:")
            for finding in lint_result.findings:
                if finding.severity == "warning":
                    click.echo(f"  WARNING: {finding.message}")
        else:
            click.echo("Linting passed with no issues!")
    except Exception as e:
        click.echo(f"Error linting configuration: {e}", err=True)
        sys.exit(1)
    
    # 4. Estimate cost
    click.echo("Estimating data ingest cost...")
    try:
        cost_req = CostRequest(
            preset_id=p.id,
            host_count=host_count,
            sample_rate=p.default_sample_rate,
            filter_patterns=p.tier1_patterns,
            filter_mode=p.filter_mode
        )
        estimate = estimate_cost(cost_req)
        
        click.echo(f"Estimated data ingest: {estimate.gib_per_day:.2f} GiB/day")
        click.echo(f"Description: {estimate.description}")
    except Exception as e:
        click.echo(f"Error estimating cost: {e}", err=True)
        sys.exit(1)
    
    # Show the generated configuration
    click.echo("\nGenerated configuration:")
    click.echo("-------------------------")
    click.echo(template_content)
    
    # 5. Perform rollout if requested
    if rollout:
        from zcp_rollout.simple_rollout import Host, rollout_config
        
        # Process host list
        target_hosts = []
        if hosts:
            target_hosts = [Host(hostname=h.strip()) for h in hosts.split(",")]
        else:
            # Use placeholder hosts for demo
            target_hosts = [Host(hostname=f"host{i}.example.com") for i in range(1, host_count + 1)]
        
        click.echo("\nRolling out configuration...")
        click.echo(f"Target hosts: {', '.join(h.hostname for h in target_hosts)}")
        
        # Roll out configuration
        try:
            summary = rollout_config(target_hosts, template_content, "infra_process.yaml", dry_run=True)
            
            # Display results
            click.echo(f"\nRollout summary: {summary.success}/{summary.total} hosts successful ({summary.success_rate:.1f}%)")
            if summary.failure > 0:
                click.echo("\nFailed hosts:")
                for hostname, result in summary.results.items():
                    if not result.success:
                        click.echo(f"  {hostname}: {result.message}")
        except Exception as e:
            click.echo(f"Error during rollout: {e}", err=True)
            sys.exit(1)
        
        # 6. Perform validation if requested
        if validate and rollout:
            from zcp_validate.simple_validate import validate_hosts
            
            click.echo("\nValidating configuration...")
            
            # Get hostnames from the target hosts
            hostnames = [h.hostname for h in target_hosts]
            
            try:
                # Validate hosts against expected data ingest
                summary = validate_hosts(
                    hosts=hostnames,
                    expected_gib_day=estimate.gib_per_day,
                    threshold=0.2  # Allow 20% deviation
                )
                
                # Display results
                click.echo(f"\nValidation summary: {summary.pass_count}/{summary.hosts_validated} hosts passed ({summary.pass_rate:.1f}%)")
                
                for hostname, result in summary.results.items():
                    status = "PASS" if result.within_threshold else "FAIL"
                    click.echo(f"  {hostname}: {status} - {result.actual_gib_day:.2f} GiB/day (expected: {result.expected_gib_day:.2f})")
            except Exception as e:
                click.echo(f"Error during validation: {e}", err=True)
                sys.exit(1)
    
    click.echo("\nWizard completed successfully!")

@cli.command()
@click.argument("file", type=click.Path(exists=True, readable=True))
def lint(file: str):
    """Lint a configuration file for issues."""
    from zcp_lint.simple_lint import lint_config
    
    # Read file
    try:
        with open(file, "r") as f:
            content = f.read()
    except Exception as e:
        click.echo(f"Error reading file: {e}", err=True)
        sys.exit(1)
    
    # Lint the file
    result = lint_config(content)
    
    # Display results
    click.echo(f"\nLint Results for {file}:")
    click.echo(f"Errors: {result.error_count}, Warnings: {result.warning_count}")
    
    if result.findings:
        click.echo("\nFindings:")
        for finding in result.findings:
            level = finding.severity.upper()
            location = f" (line {finding.line})" if finding.line is not None else ""
            click.echo(f"  {level}: {finding.message}{location}")
    else:
        click.echo("No issues found!")
    
    # Exit with error code if there are errors
    if result.error_count > 0:
        sys.exit(1)

@cli.command()
@click.option("--hosts", "-h", required=True, help="Comma-separated list of hosts")
@click.option("--config", "-c", required=True, type=click.Path(exists=True), help="Configuration file to deploy")
@click.option("--dry-run", is_flag=True, help="Simulate rollout without actually deploying")
def rollout(hosts: str, config: str, dry_run: bool):
    """Roll out a configuration to hosts."""
    from zcp_rollout.simple_rollout import Host, rollout_config
    
    # Read configuration file
    try:
        with open(config, "r") as f:
            content = f.read()
    except Exception as e:
        click.echo(f"Error reading configuration file: {e}", err=True)
        sys.exit(1)
    
    # Parse hosts
    host_list = [Host(hostname=h.strip()) for h in hosts.split(",")]
    if not host_list:
        click.echo("No hosts specified!", err=True)
        sys.exit(1)
    
    click.echo(f"Rolling out configuration to {len(host_list)} hosts...")
    if dry_run:
        click.echo("DRY RUN MODE - No actual changes will be made")
    
    # Perform rollout
    try:
        summary = rollout_config(
            hosts=host_list,
            config_content=content,
            filename=os.path.basename(config),
            dry_run=dry_run
        )
        
        # Display results
        click.echo(f"\nRollout complete: {summary.success}/{summary.total} hosts successful ({summary.success_rate:.1f}%)")
        click.echo(f"Duration: {summary.duration_ms/1000:.2f} seconds")
        
        if summary.failure > 0:
            click.echo("\nFailed hosts:")
            for hostname, result in summary.results.items():
                if not result.success:
                    click.echo(f"  {hostname}: {result.message}")
    except Exception as e:
        click.echo(f"Error during rollout: {e}", err=True)
        sys.exit(1)

@cli.command()
@click.option("--hosts", "-h", required=True, help="Comma-separated list of hosts")
@click.option("--expected", "-e", type=float, required=True, help="Expected data ingest in GiB/day")
@click.option("--threshold", "-t", type=float, default=0.2, help="Allowable deviation (0.2 = 20%)")
def validate(hosts: str, expected: float, threshold: float):
    """Validate actual data ingest against expected values."""
    from zcp_validate.simple_validate import validate_hosts
    
    # Parse hosts
    host_list = [h.strip() for h in hosts.split(",")]
    if not host_list:
        click.echo("No hosts specified!", err=True)
        sys.exit(1)
    
    click.echo(f"Validating {len(host_list)} hosts against expected ingest of {expected:.2f} GiB/day...")
    click.echo(f"Threshold: {threshold * 100:.1f}% deviation allowed")
    
    # Perform validation
    try:
        summary = validate_hosts(
            hosts=host_list,
            expected_gib_day=expected,
            threshold=threshold
        )
        
        # Display results
        click.echo(f"\nValidation complete: {summary.pass_count}/{summary.hosts_validated} hosts passed ({summary.pass_rate:.1f}%)")
        
        for hostname, result in summary.results.items():
            status = "✓" if result.within_threshold else "✗"
            click.echo(f"  {status} {hostname}: {result.actual_gib_day:.2f} GiB/day (expected: {result.expected_gib_day:.2f}, deviation: {result.deviation_percent:.1f}%)")
        
        # Exit with error code if validation failed
        if summary.fail_count > 0:
            sys.exit(1)
    except Exception as e:
        click.echo(f"Error during validation: {e}", err=True)
        sys.exit(1)

if __name__ == "__main__":
    cli()
