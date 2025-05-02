"""
Event Bus for ZCP component communication.

Provides a publish-subscribe mechanism with pluggable backends:
- SyncMem (default): In-memory synchronous event delivery
- AsyncQueue: Asynchronous delivery using asyncio.Queue
- FileTrace: JSON line-oriented event logging for troubleshooting
"""

import asyncio
import json
import logging
import os
import re
import time
from datetime import datetime
from enum import Enum
from typing import Any, Dict, List, Optional, Pattern, Protocol, Set, Union
from uuid import UUID, uuid4

from pydantic import BaseModel, Field

logger = logging.getLogger(__name__)

class Event(BaseModel):
    """Event message passed between ZCP components."""
    event_id: UUID = Field(default_factory=uuid4)
    ts: datetime = Field(default_factory=datetime.now)
    topic: str
    payload: Dict[str, Any]
    
    def __str__(self) -> str:
        return f"Event({self.topic}, {self.event_id})"

class Subscriber(Protocol):
    """Protocol for event subscribers."""
    topic: Union[str, Pattern[str]]
    
    async def handle(self, event: Event) -> None:
        """Handle an incoming event."""
        ...

class BusBackend(Protocol):
    """Protocol for event bus backends."""
    
    def publish(self, event: Event) -> None:
        """Publish an event to subscribers."""
        ...
    
    def subscribe(self, handler: Subscriber) -> None:
        """Register a subscriber."""
        ...
    
    def shutdown(self) -> None:
        """Clean shutdown of the bus."""
        ...

class SyncMemBackend:
    """In-memory synchronous event delivery."""
    
    def __init__(self):
        self._subscribers: List[Subscriber] = []
        self._loop = asyncio.get_event_loop()
    
    def publish(self, event: Event) -> None:
        """Publish event to all matching subscribers synchronously."""
        for sub in self._subscribers:
            if isinstance(sub.topic, str):
                if sub.topic == event.topic or sub.topic.endswith('*') and event.topic.startswith(sub.topic[:-1]):
                    self._loop.create_task(sub.handle(event))
            elif isinstance(sub.topic, Pattern) and sub.topic.match(event.topic):
                self._loop.create_task(sub.handle(event))
    
    def subscribe(self, handler: Subscriber) -> None:
        """Register a subscriber."""
        self._subscribers.append(handler)
    
    def shutdown(self) -> None:
        """Clean shutdown - no-op for sync backend."""
        pass

class AsyncQueueBackend:
    """Asynchronous delivery using asyncio.Queue."""
    
    def __init__(self, max_queue_size: int = 10):
        self._subscribers: List[Subscriber] = []
        self._queues: Dict[Subscriber, asyncio.Queue] = {}
        self._max_queue_size = max_queue_size
        self._tasks: Set[asyncio.Task] = set()
        self._loop = asyncio.get_event_loop()
        
    def publish(self, event: Event) -> None:
        """Queue event for asynchronous delivery."""
        for sub in self._subscribers:
            if isinstance(sub.topic, str):
                if sub.topic == event.topic or sub.topic.endswith('*') and event.topic.startswith(sub.topic[:-1]):
                    self._ensure_queue(sub).put_nowait(event)
            elif isinstance(sub.topic, Pattern) and sub.topic.match(event.topic):
                self._ensure_queue(sub).put_nowait(event)
                
    def _ensure_queue(self, sub: Subscriber) -> asyncio.Queue:
        """Create queue for subscriber if it doesn't exist."""
        if sub not in self._queues:
            queue = asyncio.Queue(maxsize=self._max_queue_size)
            self._queues[sub] = queue
            task = self._loop.create_task(self._process_queue(sub, queue))
            self._tasks.add(task)
            task.add_done_callback(self._tasks.discard)
        return self._queues[sub]
    
    async def _process_queue(self, sub: Subscriber, queue: asyncio.Queue) -> None:
        """Process events from the queue for a subscriber."""
        while True:
            event = await queue.get()
            try:
                await sub.handle(event)
            except Exception as e:
                logger.exception(f"Error in subscriber handler: {e}")
            finally:
                queue.task_done()
    
    def subscribe(self, handler: Subscriber) -> None:
        """Register a subscriber."""
        self._subscribers.append(handler)
        
    def shutdown(self) -> None:
        """Clean shutdown, cancels all tasks."""
        for task in self._tasks:
            task.cancel()

class FileTraceBackend:
    """JSON line-oriented event logging for troubleshooting."""
    
    def __init__(self, path: Optional[str] = None):
        self._path = path or os.environ.get("ZCP_TRACE_PATH", "zcp_events.jsonl")
        self._subscribers: List[Subscriber] = []
        self._loop = asyncio.get_event_loop()
        
    def publish(self, event: Event) -> None:
        """Log event to file and deliver to subscribers."""
        # Write to trace file
        with open(self._path, "a") as f:
            f.write(json.dumps({
                "event_id": str(event.event_id),
                "ts": event.ts.isoformat(),
                "topic": event.topic,
                "payload": event.payload
            }) + "\n")
            
        # Also deliver to subscribers for live processing
        for sub in self._subscribers:
            if isinstance(sub.topic, str):
                if sub.topic == event.topic or sub.topic.endswith('*') and event.topic.startswith(sub.topic[:-1]):
                    self._loop.create_task(sub.handle(event))
            elif isinstance(sub.topic, Pattern) and sub.topic.match(event.topic):
                self._loop.create_task(sub.handle(event))
    
    def subscribe(self, handler: Subscriber) -> None:
        """Register a subscriber."""
        self._subscribers.append(handler)
        
    def shutdown(self) -> None:
        """Clean shutdown - no-op for file backend."""
        pass

class BusMode(str, Enum):
    """Available bus operation modes."""
    SYNC = "sync"
    ASYNC = "async"
    TRACE = "trace"

# Global bus instance
_backend: Optional[BusBackend] = None

def _get_backend() -> BusBackend:
    """Get or initialize the bus backend."""
    global _backend
    if _backend is None:
        mode = os.environ.get("ZCP_BUS", BusMode.SYNC)
        if mode == BusMode.ASYNC:
            _backend = AsyncQueueBackend()
        elif mode == BusMode.TRACE:
            _backend = FileTraceBackend()
        else:
            _backend = SyncMemBackend()
    return _backend

def publish(event: Event) -> None:
    """Publish an event to the bus."""
    _get_backend().publish(event)

def subscribe(handler: Subscriber) -> None:
    """Register a subscriber with the bus."""
    _get_backend().subscribe(handler)

def shutdown() -> None:
    """Clean shutdown of the bus."""
    global _backend
    if _backend is not None:
        _backend.shutdown()
        _backend = None
