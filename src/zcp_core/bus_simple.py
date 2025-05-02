"""
Simplified Event Bus for ZCP component communication.

Provides a basic publish-subscribe mechanism with synchronous delivery only.
"""

import logging
from datetime import datetime
from typing import Any, Dict, List, Protocol, Union
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
    topic: str
    
    def handle(self, event: Event) -> None:
        """Handle an incoming event."""
        ...

# Global subscribers list
_subscribers: List[Subscriber] = []

def publish(event: Event) -> None:
    """
    Publish an event to subscribers synchronously.
    
    This is a simple implementation that directly calls subscribers
    in the current thread, with no async or backend complexity.
    """
    for sub in _subscribers:
        if sub.topic == event.topic or (sub.topic.endswith('*') and event.topic.startswith(sub.topic[:-1])):
            try:
                sub.handle(event)
            except Exception as e:
                logger.exception(f"Error in subscriber handler: {e}")

def subscribe(handler: Subscriber) -> None:
    """Register a subscriber with the bus."""
    _subscribers.append(handler)

def unsubscribe(handler: Subscriber) -> None:
    """Remove a subscriber from the bus."""
    if handler in _subscribers:
        _subscribers.remove(handler)
