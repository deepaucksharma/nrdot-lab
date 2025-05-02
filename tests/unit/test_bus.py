"""
Unit tests for the event bus.
"""

import asyncio
import os
import re
from datetime import datetime
from typing import List

import pytest

from zcp_core.bus import (
    AsyncQueueBackend,
    Event,
    FileTraceBackend,
    SyncMemBackend,
    _backend,
    publish,
    shutdown,
    subscribe,
)


class TestSubscriber:
    """Test subscriber for event bus tests."""
    
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
async def test_sync_backend(clean_bus):
    """Test synchronous memory backend."""
    # Set up subscribers
    sub1 = TestSubscriber("test.topic")
    sub2 = TestSubscriber("test.*")
    sub3 = TestSubscriber(re.compile(r"test\..*"))
    
    # Create backend and subscribe
    backend = SyncMemBackend()
    backend.subscribe(sub1)
    backend.subscribe(sub2)
    backend.subscribe(sub3)
    
    # Publish event
    event = Event(
        ts=datetime.now(),
        topic="test.topic",
        payload={"key": "value"}
    )
    backend.publish(event)
    
    # Allow async handlers to execute
    await asyncio.sleep(0.1)
    
    # Verify all subscribers received the event
    assert len(sub1.events) == 1
    assert len(sub2.events) == 1
    assert len(sub3.events) == 1
    
    assert sub1.events[0].event_id == event.event_id
    assert sub2.events[0].event_id == event.event_id
    assert sub3.events[0].event_id == event.event_id


@pytest.mark.asyncio
async def test_global_publish_subscribe(clean_bus):
    """Test global publish and subscribe functions."""
    # Set up subscriber
    sub = TestSubscriber("test.topic")
    
    # Subscribe
    subscribe(sub)
    
    # Publish event
    event = Event(
        ts=datetime.now(),
        topic="test.topic",
        payload={"key": "value"}
    )
    publish(event)
    
    # Allow async handlers to execute
    await asyncio.sleep(0.1)
    
    # Verify subscriber received the event
    assert len(sub.events) == 1
    assert sub.events[0].event_id == event.event_id
