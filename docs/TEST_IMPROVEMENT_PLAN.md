# Test Improvement Plan

## Current Test Coverage Status

| Component | Current Coverage | Target Coverage | Priority |
|-----------|-----------------|----------------|----------|
| zcp_core.bus | 50% | 90% | High |
| zcp_core.schema | 40% | 90% | High |
| zcp_preset | 35% | 80% | Medium |
| zcp_template | 30% | 80% | Medium |
| zcp_cost | 45% | 90% | High |
| zcp_cli | 20% | 70% | Low |
| zcp_rollout | 40% | 80% | High |
| zcp_validate | 45% | 80% | Medium |
| zcp_lint | 55% | 80% | Medium |
| zcp_logging | 30% | 80% | Medium |

## Phase 1: Critical Components (Next 2 Weeks)

Focus on high-priority components with test gaps:

### zcp_core.bus
- Complete AsyncQueueBackend tests
- Add tests for event filtering
- Test circuit breaker pattern
- Test shutdown handling

### zcp_core.schema
- Test schema versioning
- Test validation error handling
- Test schema loading from different locations
- Test nested schema references

### zcp_cost
- Test blending algorithm with different confidence levels
- Test plugin fallback scenarios
- Test with large number of plugins
- Test circuit breaker interaction with NRDB

### zcp_rollout
- Test parallel execution with various thread counts
- Test error recovery
- Test timeout handling
- Test partial success scenarios

## Phase 2: Operational Components (Weeks 3-4)

### zcp_validate
- Test threshold calculations
- Test with various NRDB response formats
- Test error handling in validation
- Test multiple host validation

### zcp_lint
- Complete rule set tests
- Test rule filtering
- Test with complex YAML structures
- Test edge cases in rules

### zcp_logging
- Test JSON formatting
- Test context binding and propagation
- Test span creation and timing
- Test OTLP integration

### zcp_preset
- Test overlay mechanism
- Test loading from multiple directories
- Test SHA-256 verification
- Test invalid preset handling

## Phase 3: Integration Testing (Weeks 5-6)

### Key Workflows
- Wizard → Render → Cost → Lint → Rollout → Validate
- Error handling across components
- Event flow through bus
- CLI command integration

### Mock Services
- NRDB mock for validation testing
- SSH server mock for rollout testing
- File system mock for configuration handling

## Phase 4: Performance Testing (Weeks 7-8)

### Benchmarks
- Large fleet rollout (10,000 hosts)
- Template rendering performance
- Cost estimation with complex histograms
- Event bus throughput

### Stress Tests
- Component behavior under high load
- Memory usage monitoring
- Resource leak detection

## Tools and Framework Enhancements

### Coverage Reporting
- Add pytest-cov to CI pipeline
- Generate HTML coverage reports
- Set coverage gates for PRs

### Test Fixtures
- Create standard test data sets
- Develop mock factories
- Add parameterized test helpers

### Test Utilities
- Create event bus test helper
- Add CLI test runner
- Develop log capture utilities

## Continuous Improvement

- Weekly test review meetings
- Test improvement tickets added to each sprint
- Test maintenance rotation among team members
- Quarterly test strategy review
