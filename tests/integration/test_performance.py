"""
Performance tests for ZCP.

These tests evaluate system performance under load:
1. Large host set rollout performance
2. Template rendering performance with complex templates
3. Cost estimation performance with many hosts
4. Event bus throughput under load
"""

import asyncio
import time
from unittest.mock import MagicMock, patch

import pytest

from zcp_core.bus import Event, EventBus, publish, subscribe
from zcp_cost.coordinator import CostCoordinator
from zcp_cost.plugin import CostRequest, StaticPlugin
from zcp_preset.loader import PresetLoader
from zcp_preset.model import Preset
from zcp_rollout.models import RolloutJob
from zcp_rollout.orchestrator import RolloutOrchestrator
from zcp_template.renderer import RenderRequest, TemplateRenderer, TokensInfra


@pytest.mark.performance
class TestPerformance:
    """Performance tests for ZCP system."""
    
    @pytest.fixture
    def test_preset(self):
        """Create a test preset."""
        return Preset(
            id="test_preset",
            default_sample_rate=15,
            filter_mode="include",
            tier1_patterns=["java", "python", "nodejs", "php", "ruby", "dotnet"],
            expected_keep_ratio=0.25,
            avg_bytes_per_sample=2048,
            sha256="test_hash"
        )
    
    @pytest.fixture
    def mock_preset_loader(self, test_preset):
        """Mock preset loader to return test preset."""
        with patch("zcp_preset.loader.PresetLoader") as mock:
            loader = mock.return_value
            loader.load.return_value = test_preset
            loader.list.return_value = ["test_preset"]
            yield loader
    
    @pytest.fixture
    def large_host_list(self):
        """Generate a large list of hosts for testing."""
        return [f"host{i}.example.com" for i in range(1, 10001)]
    
    @pytest.mark.asyncio
    async def test_event_bus_throughput(self):
        """Test event bus throughput under load."""
        # Setup event counting
        received_count = 0
        
        class CountingHandler:
            topic = "test.performance"
            
            async def handle(self, event):
                nonlocal received_count
                received_count += 1
        
        # Create async event bus
        bus = EventBus.create_async_bus()
        bus.subscribe(CountingHandler())
        
        # Start timing
        start_time = time.time()
        
        # Publish 1,000 events
        target_count = 1000
        for i in range(target_count):
            await bus.publish(Event(topic="test.performance", data={"index": i}))
        
        # Wait for events to be processed
        for _ in range(10):  # Try up to 10 times with short delays
            if received_count >= target_count:
                break
            await asyncio.sleep(0.1)
        
        end_time = time.time()
        duration = end_time - start_time
        
        # Verify performance
        events_per_second = target_count / duration
        
        assert received_count == target_count
        assert events_per_second > 500, f"Event throughput too low: {events_per_second:.2f} events/second"
        
        print(f"Event bus throughput: {events_per_second:.2f} events/second")
    
    def test_template_rendering_performance(self, mock_preset_loader):
        """Test template rendering performance with complex templates."""
        # 1. Load preset
        loader = PresetLoader()
        preset = loader.load("test_preset")
        
        # 2. Prepare complex token data with many patterns
        complex_tokens = TokensInfra(
            preset_id=preset.id,
            sample_rate=preset.default_sample_rate,
            filter_mode=preset.filter_mode,
            filter_patterns=preset.tier1_patterns + [f"process_{i}" for i in range(100)]
        )
        
        # 3. Render template (mocked)
        with patch("zcp_template.renderer.jinja2") as mock_jinja:
            # Create a template with many placeholders
            mock_template = MagicMock()
            mock_template.render.return_value = """
            integrations:
              - name: nri-process-discovery
                config:
                  interval: {{ sample_rate }}
                  discovery:
                    mode: {{ filter_mode }}
                    match_patterns:
                      {% for pattern in filter_patterns %}
                      - {{ pattern }}
                      {% endfor %}
            """
            mock_env = MagicMock()
            mock_env.get_template.return_value = mock_template
            mock_jinja.Environment.return_value = mock_env
            
            # Time the rendering process
            renderer = TemplateRenderer()
            
            iterations = 100
            start_time = time.time()
            
            for _ in range(iterations):
                render_req = RenderRequest(
                    template_id="infra_process",
                    tokens=complex_tokens
                )
                result = renderer.render(render_req)
            
            end_time = time.time()
            duration = end_time - start_time
            
            # Calculate performance metrics
            avg_render_time = (duration / iterations) * 1000  # in ms
            renders_per_second = iterations / duration
            
            # Check performance requirements
            assert avg_render_time < 100, f"Template rendering too slow: {avg_render_time:.2f} ms"
            
            print(f"Template rendering: {avg_render_time:.2f} ms per template, {renders_per_second:.2f} renders/second")
    
    def test_large_scale_rollout_performance(self, mock_preset_loader, large_host_list):
        """Test rollout performance with many hosts."""
        # 1. Generate template content
        template_content = """
        integrations:
          - name: nri-process-discovery
            config:
              interval: 15
              discovery:
                mode: include
                match_patterns:
                  - java
                  - python
        """
        
        # 2. Mock the rollout backend to be very fast
        mock_backend = MagicMock()
        mock_backend.transfer.return_value.success = True
        mock_backend.restart.return_value.success = True
        
        # 3. Create a large rollout job
        job = RolloutJob.from_host_list(
            hosts=large_host_list,
            config_content=template_content,
            filename="config.yaml",
            checksum="test_checksum",
            parallel=100  # High parallelism for performance testing
        )
        
        # 4. Time the rollout execution
        start_time = time.time()
        
        with patch("zcp_rollout.orchestrator.publish"):
            orchestrator = RolloutOrchestrator(backend=mock_backend)
            report = orchestrator.execute(job)
        
        end_time = time.time()
        duration = end_time - start_time
        
        # 5. Verify performance metrics
        hosts_per_second = len(large_host_list) / duration
        
        # Check against requirements - 10,000 hosts should take < 7 minutes
        max_allowed_duration = 7 * 60  # 7 minutes in seconds
        assert duration < max_allowed_duration, f"Rollout too slow: {duration:.2f} seconds for {len(large_host_list)} hosts"
        
        print(f"Rollout performance: {duration:.2f} seconds for {len(large_host_list)} hosts ({hosts_per_second:.2f} hosts/second)")
        
        # Verify all hosts were processed
        assert report.success == len(large_host_list)
        assert report.fail == 0
    
    def test_cost_estimation_performance(self, mock_preset_loader):
        """Test cost estimation performance with many hosts."""
        # 1. Load preset
        loader = PresetLoader()
        preset = loader.load("test_preset")
        
        # 2. Set up cost coordinator with multiple plugins
        plugins = [
            StaticPlugin(name="plugin1", confidence=0.7, gib_per_day=2.5),
            StaticPlugin(name="plugin2", confidence=0.8, gib_per_day=3.0),
            StaticPlugin(name="plugin3", confidence=0.6, gib_per_day=2.0)
        ]
        
        coordinator = CostCoordinator(plugins=plugins)
        
        # 3. Time cost estimation for various host counts
        host_counts = [100, 1000, 10000]
        
        for host_count in host_counts:
            with patch("zcp_cost.coordinator.publish"):
                # Prepare request
                cost_req = CostRequest(
                    preset_id=preset.id,
                    host_count=host_count,
                    sample_rate=preset.default_sample_rate,
                    filter_patterns=preset.tier1_patterns,
                    filter_mode=preset.filter_mode
                )
                
                # Time the estimation
                start_time = time.time()
                estimate = coordinator.estimate(cost_req)
                end_time = time.time()
                
                duration = end_time - start_time
                
                # Verify performance
                assert duration < 2.0, f"Cost estimation too slow: {duration:.2f} seconds for {host_count} hosts"
                
                print(f"Cost estimation: {duration:.2f} seconds for {host_count} hosts")
