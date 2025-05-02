# ADR 001: Event Bus Design

## Status

Accepted

## Context

The ZCP system needs a way for components to communicate with each other without tight coupling. Events need to flow between components in a flexible, extensible way that allows for different deployment topologies (single process, distributed services) and operational modes (synchronous, asynchronous, test/trace).

## Decision

We will implement an event bus with the following characteristics:

1. A simple publish-subscribe model with topic-based routing
2. Support for both string-based topics and regex pattern matching
3. Pluggable backends:
   - SyncMem: In-memory synchronous event handling
   - AsyncQueue: Asynchronous delivery with queuing
   - FileTrace: JSON line-based event logging for diagnostics and replay

The bus will be configurable via environment variables (ZCP_BUS=sync|async|trace) and will have a clean global interface to hide implementation details from components.

## Consequences

### Positive

- Components are decoupled, only depending on the event contract
- Easy to test components in isolation
- Flexible deployment options
- Built-in tracing for troubleshooting
- Scalable to async mode for high-throughput scenarios

### Negative

- Additional complexity compared to direct method calls
- Potential for "event spaghetti" if overused
- Asynchronous operations can make debugging more challenging

## Reviewers

- ☑ SRE
- ☑ FinOps
- ☑ Sec-ops
