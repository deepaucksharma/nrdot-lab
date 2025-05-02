"""
Extended unit tests for the event bus.

These tests focus on edge cases, error handling, and complex routing scenarios
that were identified as gaps in the test coverage.
"""

import asyncio
import os
import re
import tempfile
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Optional
from unittest.mock import MagicMock, patch

import pytest

from zcp_core.bus import (
    AsyncQueueBackend,
    Event,
    EventBus,
    FileTraceBackend,
    SyncMemBackend,
    _backend,
    create_event,
    publish,
    shutdown,
    subscribe,
)


class FailingSubscriber:
    """Test subscriber that raises exceptions during handling."""
    
    def __init__(self, topic, fail_pattern=None):
        self.topic = topic
        self.events: List[Event] = []
        self.errors: List[Exception] = []
        self.fail_pattern = fail_pattern or "*"
        
    async def handle(self, event: Event) -> None:
        self.events.append(event)
        
        # Fail if topic matches pattern
        if isinstance(self.fail_pattern, str) and self.fail_pattern == "*":
            raise ValueError(f"Test failure handling {event.topic}")
        elif isinstance(self.fail_pattern, str) and self.fail_pattern in event.topic:
            raise ValueError(f"Test failure handling {event.topic}")
        elif isinstance(self.fail_pattern, re.Pattern) and self.fail_pattern.match(event.topic):
            raise ValueError(f"Test failure handling {event.topic}")


class SlowSubscriber:
    """Test subscriber with slow handling for testing concurrency."""
    
    def __init__(self, topic, delay_seconds=0.1):
        self.topic = topic
        self.events: List[Event] = []
        self.delay = delay_seconds
        self.started_at: Dict[str, float] = {}
        self.completed_at: Dict[str, float] = {}
        
    async def handle(self, event: Event) -> None:
        import time
        
        # Record start time
        self.started_at[event.event_id] = time.time()
        
        # Simulate processing delay
        await asyncio.sleep(self.delay)
        
        # Store event and completion time
        self.events.append(event)
        self.completed_at[event.event_id] = time.time()


class OrderingSubscriber:
    """Test subscriber that tracks the order of events."""
    
    def __init__(self, topic):
        self.topic = topic
        self.events: List[Event] = []
        
    async def handle(self, event: Event) -> None:
        self.events.append(event)


@pytest.fixture
def clean_bus():
    """Fixture to ensure a clean bus for each test."""
    # Clear any existing backend
    global _backend
    _backend = None
    
    # Ensure environment is clean
    os.environ.pop("ZCP_BUS", None)
    
    yield
    
    # Clean up after test
    shutdown()


@pytest.mark.asyncio
async def test_event_creation():
    """Test event creation with various parameters."""
    # Basic event creation
    event = create_event("test.topic", {"key": "value"})
    assert event.topic == "test.topic"
    assert event.payload == {"key": "value"}
    assert event.ts is not None
    assert event.event_id is not None
    
    # Custom timestamp
    now = datetime.now()
    event = create_event("test.topic", {"key": "value"}, ts=now)
    assert event.ts == now
    
    # Custom event ID
    event = create_event("test.topic", {"key": "value"}, event_id="custom-id")
    assert event.event_id == "custom-id"


@pytest.mark.asyncio
async def test_error_handling_in_sync_backend(clean_bus):
    """Test error handling in synchronous backend."""
    # Set up a failing subscriber
    failing_sub = FailingSubscriber("test.topic")
    
    # Create backend and subscribe
    backend = SyncMemBackend()
    backend.subscribe(failing_sub)
    
    # Publish event - should not crash despite handler error
    event = Event(
        ts=datetime.now(),
        topic="test.topic",
        payload={"key": "value"}
    )
    
    with patch("zcp_core.bus.logger") as mock_logger:
        backend.publish(event)
        
        # Allow async handlers to execute
        await asyncio.sleep(0.1)
        
        # Verify error was logged
        mock_logger.error.assert_called()
        
        # Verify the event was still received
        assert len(failing_sub.events) == 1
        assert failing_sub.events[0].event_id == event.event_id


@pytest.mark.asyncio
async def test_async_backend_concurrency(clean_bus):
    """Test concurrent event handling in async backend."""
    # Set up multiple slow subscribers
    sub1 = SlowSubscriber("test.topic", delay_seconds=0.2)
    sub2 = SlowSubscriber("test.topic", delay_seconds=0.2)
    sub3 = SlowSubscriber("other.topic", delay_seconds=0.2)
    
    # Create async backend and subscribe
    backend = AsyncQueueBackend()
    backend.subscribe(sub1)
    backend.subscribe(sub2)
    backend.subscribe(sub3)
    
    # Publish events to different topics
    events = [
        Event(ts=datetime.now(), topic="test.topic", payload={"index": 1}),
        Event(ts=datetime.now(), topic="test.topic", payload={"index": 2}),
        Event(ts=datetime.now(), topic="other.topic", payload={"index": 3})
    ]
    
    # Publish all events rapidly
    for event in events:
        backend.publish(event)
    
    # Wait for all events to be processed
    await asyncio.sleep(0.5)
    
    # Verify events were delivered
    assert len(sub1.events) == 2  # test.topic events
    assert len(sub2.events) == 2  # test.topic events
    assert len(sub3.events) == 1  # other.topic event
    
    # Verify concurrent processing by checking timing
    # Events for same subscriber should be handled sequentially
    if len(sub1.completed_at) >= 2:
        event_ids = [e.event_id for e in sub1.events]
        first_completed = sub1.completed_at[event_ids[0]]
        second_started = sub1.started_at[event_ids[1]]
        
        # Second event should start after first completes
        assert second_started >= first_completed


@pytest.mark.asyncio
async def test_complex_topic_routing(clean_bus):
    """Test complex topic routing with regex patterns."""
    # Set up subscribers with various patterns
    exact_match = OrderingSubscriber("system.component.action")
    prefix_match = OrderingSubscriber("system.component.*")
    suffix_match = OrderingSubscriber("*.*.action")
    regex_match = OrderingSubscriber(re.compile(r"system\..*\.action"))
    middle_wildcard = OrderingSubscriber("system.*.action")
    all_events = OrderingSubscriber("*")
    
    # Create backend and subscribe all
    backend = SyncMemBackend()
    backend.subscribe(exact_match)
    backend.subscribe(prefix_match)
    backend.subscribe(suffix_match)
    backend.subscribe(regex_match)
    backend.subscribe(middle_wildcard)
    backend.subscribe(all_events)
    
    # Publish events to test routing
    events = [
        Event(ts=datetime.now(), topic="system.component.action", payload={"test": 1}),
        Event(ts=datetime.now(), topic="system.component.status", payload={"test": 2}),
        Event(ts=datetime.now(), topic="system.other.action", payload={"test": 3}),
        Event(ts=datetime.now(), topic="app.component.action", payload={"test": 4})
    ]
    
    for event in events:
        backend.publish(event)
    
    # Allow async handlers to execute
    await asyncio.sleep(0.1)
    
    # Verify event routing
    assert len(exact_match.events) == 1  # Only "system.component.action"
    assert exact_match.events[0].topic == "system.component.action"
    
    assert len(prefix_match.events) == 2  # "system.component.*"
    assert all(e.topic.startswith("system.component.") for e in prefix_match.events)
    
    assert len(suffix_match.events) == 3  # "*.*action"
    assert all(e.topic.endswith(".action") for e in suffix_match.events)
    
    assert len(regex_match.events) == 2  # "system.*.action"
    assert all(e.topic.startswith("system.") and e.topic.endswith(".action") for e in regex_match.events)
    
    assert len(middle_wildcard.events) == 2  # "system.*.action" 
    assert all(e.topic.startswith("system.") and e.topic.endswith(".action") for e in middle_wildcard.events)
    
    assert len(all_events.events) == 4  # All events


@pytest.mark.asyncio
async def test_file_trace_backend(clean_bus):
    """Test the file trace backend."""
    # Create a temporary file for testing
    with tempfile.NamedTemporaryFile(delete=False) as tmp:
        trace_file = tmp.name
    
    try:
        # Create a file trace backend
        backend = FileTraceBackend(Path(trace_file))
        
        # Create event
        event = Event(
            ts=datetime.now(),
            topic="test.topic",
            payload={"key": "value"}
        )
        
        # Publish event
        backend.publish(event)
        
        # Publish another event
        another_event = Event(
            ts=datetime.now(),
            topic="another.topic",
            payload={"another": "value"}
        )
        backend.publish(another_event)
        
        # Read the trace file
        with open(trace_file, "r") as f:
            content = f.read()
        
        # Verify both events were written to the file
        assert event.event_id in content
        assert event.topic in content
        assert another_event.event_id in content
        assert another_event.topic in content
        
    finally:
        # Clean up the temporary file
        if os.path.exists(trace_file):
            os.unlink(trace_file)


@pytest.mark.asyncio
async def test_event_bus_factory(clean_bus):
    """Test the EventBus factory methods."""
    # Test creating sync bus
    sync_bus = EventBus.create_sync_bus()
    assert isinstance(sync_bus._backend, SyncMemBackend)
    
    # Test creating async bus
    async_bus = EventBus.create_async_bus()
    assert isinstance(async_bus._backend, AsyncQueueBackend)
    
    # Test creating trace bus
    with tempfile.NamedTemporaryFile(delete=False) as tmp:
        trace_file = tmp.name
    
    try:
        trace_bus = EventBus.create_trace_bus(Path(trace_file))
        assert isinstance(trace_bus._backend, FileTraceBackend)
    finally:
        if os.path.exists(trace_file):
            os.unlink(trace_file)


@pytest.mark.asyncio
async def test_event_ordering(clean_bus):
    """Test event ordering is maintained."""
    # Set up subscriber
    sub = OrderingSubscriber("test.topic")
    
    # Create backend and subscribe
    backend = SyncMemBackend()
    backend.subscribe(sub)
    
    # Publish 100 ordered events
    events = []
    for i in range(100):
        event = Event(
            ts=datetime.now(),
            topic="test.topic",
            payload={"index": i}
        )
        events.append(event)
        backend.publish(event)
    
    # Allow async handlers to execute
    await asyncio.sleep(0.1)
    
    # Verify events were received in order
    assert len(sub.events) == 100
    for i, event in enumerate(sub.events):
        assert event.payload["index"] == i


@pytest.mark.asyncio
async def test_subscriber_unsubscribe(clean_bus):
    """Test unsubscribing subscribers."""
    # Set up subscribers
    sub1 = OrderingSubscriber("test.topic")
    sub2 = OrderingSubscriber("test.topic")
    
    # Create backend and subscribe
    backend = SyncMemBackend()
    backend.subscribe(sub1)
    backend.subscribe(sub2)
    
    # Publish event - both should receive
    event1 = Event(
        ts=datetime.now(),
        topic="test.topic",
        payload={"key": "value1"}
    )
    backend.publish(event1)
    
    # Allow async handlers to execute
    await asyncio.sleep(0.1)
    
    # Verify both received
    assert len(sub1.events) == 1
    assert len(sub2.events) == 1
    
    # Unsubscribe sub1
    backend.unsubscribe(sub1)
    
    # Publish another event - only sub2 should receive
    event2 = Event(
        ts=datetime.now(),
        topic="test.topic",
        payload={"key": "value2"}
    )
    backend.publish(event2)
    
    # Allow async handlers to execute
    await asyncio.sleep(0.1)
    
    # Verify only sub2 received the second event
    assert len(sub1.events) == 1  # Still only 1 event
    assert len(sub2.events) == 2  # Now has 2 events
