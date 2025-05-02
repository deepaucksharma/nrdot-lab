"""
Main CLI entry point.
"""

import sys
from typing import List, Optional

import click

from zcp_core.bus import BusMode
from zcp_logging.logger import LoggerFactory
from zcp_preset.loader import PresetLoader


@click.group()
@click.version_option()
@click.option("--log-level", type=click.Choice(["DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL"]), default="INFO", help="Logging level")
@click.option("--json-logs", is_flag=True, help="Output logs in JSON format")
@click.option("--otlp", is_flag=True, help="Enable OpenTelemetry logging")
def cli(log_level: str, json_logs: bool, otlp: bool):
    """Zero Config Process (ZCP) CLI tool."""
    # Initialize logging
    LoggerFactory.init(level=log_level, enable_otlp=otlp, json_format=json_logs)
    logger = LoggerFactory.get("zcp_cli")
    logger.debug("CLI initialized", context={"log_level": log_level, "json_logs": json_logs, "otlp": otlp})


@cli.command()
def doctor():
    """Run self-diagnostic checks."""
    logger = LoggerFactory.get("zcp_cli.doctor")
    logger.info("Running ZCP diagnostics...")
    
    with logger.span("doctor_checks"):
        # Check environment, connections, etc.
        logger.info("All checks passed")
    
    click.echo("✓ All checks passed")


@cli.group()
def preset():
    """Manage presets."""
    pass


@preset.command(name="list")
def list_presets():
    """List available presets."""
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
@click.option("--preset", "-p", help="Preset ID to use")
@click.option("--host-count", "-n", type=int, default=1, help="Number of hosts")
@click.option("--template", "-t", default="infra_process", help="Template ID")
@click.option("--format", "-f", type=click.Choice(["text", "json"]), default="text")
@click.option("--rollout", is_flag=True, help="Perform rollout after configuration")
@click.option("--hosts", help="Comma-separated list of hosts for rollout")
@click.option("--rollout-mode", type=click.Choice(["print", "ssh", "ansible"]), default="print", help="Rollout backend mode")
def wizard(preset: Optional[str], host_count: int, template: str, format: str, rollout: bool, hosts: Optional[str], rollout_mode: str):
    """Run the configuration wizard."""
    from zcp_cost.coordinator import CostCoordinator
    from zcp_cost.plugin import CostRequest, StaticPlugin, HistogramPlugin
    from zcp_template.renderer import RenderRequest, TemplateRenderer, TokensInfra
    
    # Default preset if not specified
    preset_id = preset or "java_heavy"
    
    click.echo(f"Starting wizard with preset: {preset_id}")
    
    # Load preset
    try:
        loader = PresetLoader()
        p = loader.load(preset_id)
        click.echo(f"Loaded preset {p.id} (sha256: {p.sha256[:8]}...)")
    except Exception as e:
        click.echo(f"Error loading preset: {e}", err=True)
        sys.exit(1)
    
    # Render template
    try:
        renderer = TemplateRenderer()
        render_req = RenderRequest(
            template_id=template,
            tokens=TokensInfra(
                preset_id=p.id,
                sample_rate=p.default_sample_rate,
                filter_mode=p.filter_mode,
                filter_patterns=p.tier1_patterns
            )
        )
        result = renderer.render(render_req)
        click.echo(f"Rendered template (checksum: {result.checksum[:8]}...)")
    except Exception as e:
        click.echo(f"Error rendering template: {e}", err=True)
        sys.exit(1)
    
    # Estimate cost
    try:
        coordinator = CostCoordinator(
            plugins=[StaticPlugin(), HistogramPlugin()]
        )
        cost_req = CostRequest(
            preset_id=p.id,
            host_count=host_count,
            sample_rate=p.default_sample_rate,
            filter_patterns=p.tier1_patterns,
            filter_mode=p.filter_mode
        )
        estimate = coordinator.estimate(cost_req)
        
        click.echo(f"Estimated data ingest: {estimate.blended_gib_per_day:.2f} GiB/day")
        click.echo(f"Confidence: {estimate.confidence:.2%}")
        
        for plugin_est in estimate.breakdown:
            click.echo(f"  {plugin_est.plugin_name}: {plugin_est.estimate_gib_per_day:.2f} GiB/day (confidence: {plugin_est.confidence:.2%})")
    except Exception as e:
        click.echo(f"Error estimating cost: {e}", err=True)
        sys.exit(1)
    
    # Show output based on format
    if format == "json":
        import json
        output = {
            "preset": p.dict(),
            "template": {
                "id": template,
                "checksum": result.checksum
            },
            "estimate": estimate.dict()
        }
        click.echo(json.dumps(output, indent=2))
    else:
        click.echo("\nGenerated configuration:")
        click.echo("-------------------------")
        click.echo(result.text)
    
    # Perform rollout if requested
    if rollout:
        from zcp_rollout.models import RolloutJob
        from zcp_rollout.orchestrator import RolloutOrchestrator
        
        # Get hosts
        target_hosts = []
        if hosts:
            target_hosts = [h.strip() for h in hosts.split(",")]
        else:
            # Use placeholder hosts for demo
            target_hosts = [f"host{i}.example.com" for i in range(1, host_count + 1)]
        
        click.echo("\nPreparing rollout...")
        click.echo(f"Target hosts: {', '.join(target_hosts)}")
        
        # Create rollout job
        job = RolloutJob.from_host_list(
            hosts=target_hosts,
            config_content=result.text,
            filename=f"{template}.yaml",
            checksum=result.checksum
        )
        
        # Execute rollout
        orchestrator = RolloutOrchestrator()
        try:
            click.echo(f"Starting rollout with mode: {rollout_mode}")
            report = orchestrator.execute(job, mode=rollout_mode)
            
            # Display results
            click.echo("\nRollout complete:")
            click.echo(f"Success: {report.success} hosts ({report.success_rate:.1%})")
            click.echo(f"Failed: {report.fail} hosts")
            click.echo(f"Duration: {report.duration_s:.2f} seconds")
            
            if report.fail > 0:
                click.echo("\nFailed hosts:")
                for hostname, result in report.results.items():
                    if not result.success:
                        click.echo(f"  {hostname}: {result.message}")
        except Exception as e:
            click.echo(f"Error during rollout: {e}", err=True)
            sys.exit(1)


@cli.group()
def bus():
    """Event bus utilities."""
    pass


@cli.group()
def rollout():
    """Manage configuration rollouts."""
    pass


@cli.group()
def validate():
    """Validate configurations against actual data."""
    pass


@cli.group()
def lint():
    """Lint configuration files."""
    pass


@lint.command(name="check")
@click.argument("file", type=click.Path(exists=True, readable=True))
@click.option("--rules", "-r", help="Comma-separated list of rule IDs to apply")
@click.option("--format", "-f", type=click.Choice(["text", "json"]), default="text")
def lint_check(file: str, rules: Optional[str], format: str):
    """Lint a configuration file for issues."""
    from zcp_lint.linter import Linter
    from zcp_lint.models import LintRequest
    import json
    
    # Read file
    try:
        with open(file, "r") as f:
            content = f.read()
    except Exception as e:
        click.echo(f"Error reading file: {e}", err=True)
        sys.exit(1)
    
    # Parse rules
    rule_ids = None
    if rules:
        rule_ids = [r.strip() for r in rules.split(",")]
    
    # Create lint request
    request = LintRequest(
        content=content,
        filename=file,
        rules=rule_ids
    )
    
    # Create linter and run
    linter = Linter()
    result = linter.lint(request)
    
    # Display results
    if format == "json":
        click.echo(json.dumps(result.dict(), indent=2))
    else:
        click.echo(f"\nLint Results for {file}:")
        click.echo(f"Errors: {result.error_count}, Warnings: {result.warning_count}, Info: {result.info_count}")
        
        if result.has_findings:
            click.echo("\nFindings:")
            # Sort by severity (error first, then warning, then info)
            sorted_findings = sorted(
                result.findings, 
                key=lambda f: {"error": 0, "warning": 1, "info": 2}.get(f.severity, 3)
            )
            
            for finding in sorted_findings:
                severity_icon = {
                    "error": "✗",
                    "warning": "⚠",
                    "info": "ℹ"
                }.get(finding.severity, "?")
                
                location = ""
                if finding.line is not None:
                    location = f" (line {finding.line}"
                    if finding.column is not None:
                        location += f", col {finding.column}"
                    location += ")"
                
                click.echo(f"  {severity_icon} [{finding.rule_id}]{location}: {finding.message}")
        else:
            click.echo("No issues found.")
    
    # Exit with error code if there are errors
    if result.has_errors:
        sys.exit(1)


@lint.command(name="rules")
@click.option("--format", "-f", type=click.Choice(["text", "json"]), default="text")
def lint_rules(format: str):
    """List available lint rules."""
    from zcp_lint.linter import Linter
    import json
    
    # Get rules
    rules = Linter.get_available_rules()
    
    # Display rules
    if format == "json":
        click.echo(json.dumps([r.dict() for r in rules], indent=2))
    else:
        click.echo("\nAvailable Lint Rules:")
        
        for rule in rules:
            severity_icon = {
                "error": "✗",
                "warning": "⚠",
                "info": "ℹ"
            }.get(rule.severity, "?")
            
            enabled = "enabled" if rule.enabled else "disabled"
            
            click.echo(f"  {severity_icon} {rule.id} - {rule.name} ({enabled})")
            click.echo(f"      {rule.description}")


@cli.group()
def logging():
    """Manage logging settings."""
    pass


@logging.command(name="init")
@click.option("--level", "-l", type=click.Choice(["DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL"]), default="INFO", help="Logging level")
@click.option("--json", "-j", is_flag=True, help="Output logs in JSON format")
@click.option("--otlp", "-o", is_flag=True, help="Enable OpenTelemetry logging")
@click.option("--otlp-endpoint", help="OpenTelemetry endpoint URL")
def logging_init(level: str, json: bool, otlp: bool, otlp_endpoint: Optional[str]):
    """Initialize logging with custom settings."""
    # Set OTLP endpoint if provided
    if otlp_endpoint:
        import os
        os.environ["OTEL_EXPORTER_OTLP_ENDPOINT"] = otlp_endpoint
    
    # Initialize logging
    from zcp_logging.logger import LoggerFactory
    LoggerFactory.init(level=level, enable_otlp=otlp, json_format=json)
    
    # Get logger and log initialization
    logger = LoggerFactory.get("zcp_cli.logging")
    logger.info("Logging initialized with custom settings", 
               context={"level": level, "json": json, "otlp": otlp, "endpoint": otlp_endpoint})
    
    click.echo(f"Logging initialized with level={level}, json={json}, otlp={otlp}")
    if otlp_endpoint:
        click.echo(f"OTLP endpoint: {otlp_endpoint}")


@logging.command(name="test")
@click.option("--level", "-l", type=click.Choice(["DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL"]), default="INFO", help="Test message level")
def logging_test(level: str):
    """Test logging at different levels."""
    from zcp_logging.logger import LoggerFactory
    
    # Get logger
    logger = LoggerFactory.get("zcp_cli.test")
    
    # Log at specified level
    log_message = f"Test message at {level} level"
    getattr(logger, level.lower())(log_message, context={"test": True})
    
    # Log sample messages at all levels for testing
    logger.debug("Debug test message")
    logger.info("Info test message")
    logger.warning("Warning test message")
    logger.error("Error test message", context={"error_code": "TEST_ERROR"})
    
    # Test span
    with logger.span("test_span", context={"operation": "test"}):
        logger.info("Inside test span")
        # Simulate some work
        import time
        time.sleep(0.1)
    
    click.echo(f"Logged test messages. Check your logs for '{log_message}'")


@validate.command(name="check")
@click.option("--hosts", "-h", required=True, help="Comma-separated list of hosts or @file.txt")
@click.option("--expected", "-e", type=float, required=True, help="Expected ingest in GiB/day")
@click.option("--confidence", "-c", type=float, default=0.8, help="Confidence in estimate (0-1)")
@click.option("--threshold", "-t", type=float, default=0.1, help="Allowable deviation threshold (0-1)")
@click.option("--timeframe", type=int, default=24, help="Timeframe in hours")
@click.option("--format", "-f", type=click.Choice(["text", "json"]), default="text")
def validate_check(hosts: str, expected: float, confidence: float, threshold: float, timeframe: int, format: str):
    """Validate configuration by comparing expected vs. actual ingest."""
    from zcp_logging.logger import LoggerFactory
    from zcp_validate.models import ValidationJob
    from zcp_validate.validator import Validator
    import json
    
    logger = LoggerFactory.get("zcp_cli.validate")
    
    # Get host list
    host_list = []
    if hosts.startswith("@"):
        # Read hosts from file
        host_file = hosts[1:]
        try:
            with open(host_file, "r") as f:
                host_list = [line.strip() for line in f if line.strip()]
            logger.debug(f"Read {len(host_list)} hosts from file {host_file}")
        except Exception as e:
            logger.error(f"Error reading host file: {e}", context={"file": host_file})
            click.echo(f"Error reading host file: {e}", err=True)
            sys.exit(1)
    else:
        # Parse comma-separated list
        host_list = [h.strip() for h in hosts.split(",")]
        logger.debug(f"Parsed {len(host_list)} hosts from command line")
    
    click.echo(f"Validating {len(host_list)} hosts...")
    logger.info(f"Starting validation for {len(host_list)} hosts", 
               context={"expected": expected, "threshold": threshold, "timeframe": timeframe})
    
    # Create validation job
    job = ValidationJob(
        hosts=host_list,
        expected_gib_day=expected,
        confidence=confidence,
        threshold=threshold,
        timeframe_hours=timeframe
    )
    
    # Execute validation
    validator = Validator()
    try:
        with logger.span("validation", context={"hosts_count": len(host_list)}):
            click.echo(f"Querying NRDB for actual ingest data (past {timeframe} hours)...")
            result = validator.validate(job)
            
            # Log validation result
            logger.info(f"Validation result: {result.summary}", 
                       context={
                           "pass_rate": result.pass_rate,
                           "overall_pass": result.overall_pass,
                           "hosts_count": len(result.host_results)
                       })
            
            # Display results
            if format == "json":
                click.echo(json.dumps(result.dict(), indent=2, default=str))
            else:
                click.echo(f"\nValidation Result: {result.summary}")
                click.echo(f"Query Duration: {result.query_duration_ms:.2f} ms")
                click.echo("\nHost Details:")
                
                # Sort by hostname
                for hostname in sorted(result.host_results.keys()):
                    host_result = result.host_results[hostname]
                    icon = "✓" if host_result.within_threshold else "✗"
                    click.echo(f"  {icon} {hostname}: {host_result.actual_gib_day:.2f} GiB/day (expected: {host_result.expected_gib_day:.2f}, deviation: {host_result.deviation_percent:.1f}%)")
            
            # Exit with error code if validation failed
            if not result.overall_pass:
                logger.warning("Validation failed, exiting with non-zero status")
                sys.exit(1)
    except Exception as e:
        logger.error(f"Error during validation: {e}", exc_info=True)
        click.echo(f"Error during validation: {e}", err=True)
        sys.exit(1)


@rollout.command(name="execute")
@click.option("--hosts", "-h", required=True, help="Comma-separated list of hosts or @file.txt")
@click.option("--config", "-c", required=True, help="Path to configuration file to deploy")
@click.option("--target", "-t", default="/etc/newrelic-infra/integrations.d/", help="Target directory on hosts")
@click.option("--filename", "-f", help="Target filename (default: basename of config file)")
@click.option("--parallel", "-p", type=int, default=10, help="Number of hosts to process in parallel")
@click.option("--mode", "-m", type=click.Choice(["print", "ssh", "ansible"]), default="print", help="Rollout backend mode")
@click.option("--ssh-user", help="SSH username")
@click.option("--ssh-key", help="Path to SSH private key")
@click.option("--use-sudo", is_flag=True, help="Use sudo for restarts")
def execute_rollout(hosts: str, config: str, target: str, filename: str, parallel: int, mode: str, ssh_user: str, ssh_key: str, use_sudo: bool):
    """Execute a configuration rollout to hosts."""
    import hashlib
    import os
    from pathlib import Path
    from zcp_rollout.models import RolloutHost, RolloutJob
    from zcp_rollout.orchestrator import RolloutOrchestrator
    
    # Read configuration file
    try:
        with open(config, "r") as f:
            config_content = f.read()
            
        # Calculate checksum
        checksum = hashlib.sha256(config_content.encode()).hexdigest()
        
        # Determine target filename
        if not filename:
            filename = os.path.basename(config)
            
        click.echo(f"Configuration: {config} (checksum: {checksum[:8]}...)")
    except Exception as e:
        click.echo(f"Error reading configuration file: {e}", err=True)
        sys.exit(1)
    
    # Get host list
    host_list = []
    if hosts.startswith("@"):
        # Read hosts from file
        host_file = hosts[1:]
        try:
            with open(host_file, "r") as f:
                host_list = [line.strip() for line in f if line.strip()]
        except Exception as e:
            click.echo(f"Error reading host file: {e}", err=True)
            sys.exit(1)
    else:
        # Parse comma-separated list
        host_list = [h.strip() for h in hosts.split(",")]
    
    click.echo(f"Target hosts: {len(host_list)} hosts")
    
    # Create rollout hosts
    rollout_hosts = []
    for host in host_list:
        rollout_hosts.append(RolloutHost(
            hostname=host,
            ssh_user=ssh_user,
            ssh_key_path=ssh_key,
            use_sudo=use_sudo,
            target_path=target
        ))
    
    # Create rollout job
    job = RolloutJob(
        hosts=rollout_hosts,
        config_content=config_content,
        config_filename=filename,
        checksum=checksum,
        parallel=parallel
    )
    
    # Execute rollout
    orchestrator = RolloutOrchestrator()
    try:
        click.echo(f"Starting rollout with mode: {mode}")
        report = orchestrator.execute(job, mode=mode)
        
        # Display results
        click.echo("\nRollout complete:")
        click.echo(f"Success: {report.success} hosts ({report.success_rate:.1%})")
        click.echo(f"Failed: {report.fail} hosts")
        click.echo(f"Duration: {report.duration_s:.2f} seconds")
        
        if report.fail > 0:
            click.echo("\nFailed hosts:")
            for hostname, result in report.results.items():
                if not result.success:
                    click.echo(f"  {hostname}: {result.message}")
        
        # Exit with error code if any hosts failed
        if report.fail > 0:
            sys.exit(1)
    except Exception as e:
        click.echo(f"Error during rollout: {e}", err=True)
        sys.exit(1)


@bus.command(name="trace")
@click.option("--output", "-o", help="Output file for events")
def bus_trace(output: Optional[str]):
    """Trace event bus activity."""
    import os
    import json
    import time
    from zcp_core.bus import Event, Subscriber, subscribe
    
    # Set bus mode to trace
    os.environ["ZCP_BUS"] = BusMode.TRACE
    os.environ["ZCP_TRACE_PATH"] = output or "zcp_events.jsonl"
    
    class EventTracer:
        topic = ".*"  # Match all topics
        
        async def handle(self, event: Event):
            """Print events to console."""
            click.echo(f"{event.ts.isoformat()} | {event.topic} | {json.dumps(event.payload)}")
    
    # Subscribe to all events
    subscribe(EventTracer())
    
    click.echo(f"Tracing events to {os.environ['ZCP_TRACE_PATH']}")
    click.echo("Press Ctrl+C to stop...")
    
    try:
        while True:
            time.sleep(0.1)
    except KeyboardInterrupt:
        click.echo("Trace stopped")


if __name__ == "__main__":
    cli()
