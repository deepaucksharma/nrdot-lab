# Critical Functional Issues Fixed

This document summarizes the critical functional issues that have been fixed in the codebase.

## 1. Data-model/Schema Mismatches

Fixed the snake_case vs camelCase inconsistency between the Python models and JSON schemas:

- Updated `CostEstimate` and `PluginEstimate` models to use proper alias generation
- Added `by_alias=True` to dict() serialization for schema validation compatibility
- Ensured model fields match their schema counterparts

## 2. Event Bus Delivery Problems

Fixed several critical issues with the event bus:

- Made async task handling in `SyncMemBackend` and `FileTraceBackend` properly await tasks
- Added exception handling for `QueueFull` in `AsyncQueueBackend`
- Implemented `unsubscribe()` methods to prevent memory leaks
- Created both async and sync publish methods

## 3. CircuitBreaker Reset Logic

Fixed the CircuitBreaker in nrdb_client.py:

- Fixed the `open_since` tracking to use `None` for closed circuit state
- Added a proper `reset()` method that clears both failure count and open state
- Corrected the time comparison logic to prevent negative calculations

## 4. Testing Artifacts Not Compiling

Fixed integration test compatibility issues:

- Updated `test_error_recovery_flow.py` to use the `RolloutReport` model instead of the non-existent `RolloutResult`
- Fixed the mock function to use the correct `HostResult` model
- Added a comprehensive test suite to verify all imports work correctly

## 5. Python 3.11+ Compatibility

Added compatibility code for Python 3.11+:

- Created a `get_or_create_loop()` function that works around the deprecation of `asyncio.get_event_loop()`
- Updated all event loop initializations to use the new function
- Fixed the publish methods to handle async/sync contexts properly

## 6. Pydantic v1 to v2 Compatibility

Created a forward-compatible solution for Pydantic:

- Updated pyproject.toml to allow both Pydantic v1 and v2
- Created a compatibility layer in `zcp_core.compat` that works with both versions
- Added a `PydanticCompatModel` to bridge the API differences between versions

## 7. Resource Loading

Improved resource loading for packaged installations:

- Created a `resource.py` module with utilities for accessing packaged resources
- Added support for importlib.resources which works in wheel packages
- Implemented fallback mechanisms for development mode

## 8. Packaging Improvements

Updated wheel packaging to include all necessary files:

- Added templates, schemas, presets, and runbooks to the wheel package
- Set up proper include/exclude patterns for artifacts
- Made sure the distribution contains all files needed for runtime

## 9. Testing Improvements

Added new tests to verify functional correctness:

- Created `test_imports.py` to check that all modules import correctly
- Added specific tests for critical model imports
- Improved the tests to catch future regressions

These fixes address the most critical functional issues in the codebase, focusing on runtime stability, compatibility, and correctness.
