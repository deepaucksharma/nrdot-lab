# ZCP Test Improvement Plan

## Current Test Coverage Assessment

As of May 2, 2025, the test coverage across the ZCP project is approximately 40%. This assessment is based on:

- Analysis of existing test files
- Coverage reports from recent test runs
- Identification of untested critical paths

### Coverage by Component

| Component | Current Coverage | Target Coverage | Priority |
|-----------|-----------------|----------------|----------|
| zcp_core.bus | 65% | 90% | High |
| zcp_core.schema | 45% | 85% | High |
| zcp_preset | 50% | 80% | Medium |
| zcp_template | 40% | 80% | Medium |
| zcp_cost | 35% | 85% | High |
| zcp_rollout | 30% | 80% | High |
| zcp_validate | 35% | 80% | High |
| zcp_lint | 45% | 75% | Medium |
| zcp_logging | 40% | 70% | Low |
| zcp_cli | 25% | 75% | Medium |

## Critical Gaps Identified

1. **Event Bus**: Missing tests for error handling and async edge cases
2. **Cost Estimation**: Limited testing of complex scenarios and plugin interactions
3. **Rollout Module**: Insufficient testing of failure modes and recovery paths
4. **Validation Logic**: Missing tests for threshold validation and complex queries
5. **Integration Tests**: Only one end-to-end workflow test exists
6. **Performance Tests**: No systematic performance testing implemented

## Phased Improvement Plan

### Phase 1: Core Component Coverage (Week 1)

Focus on bringing the most critical components up to 75%+ coverage:

1. **zcp_core.bus**
   - Add tests for error handling in all backends
   - Test event routing with complex event hierarchies
   - Test concurrent event publishing scenarios
   - Complete AsyncQueueBackend tests
   - Test circuit breaker pattern
   - Test shutdown handling

2. **zcp_core.schema**
   - Test schema versioning
   - Test validation error handling
   - Test schema loading from different locations
   - Test nested schema references

3. **zcp_cost**
   - Add tests for all cost plugins
   - Test confidence blending algorithm
   - Test cost estimation with varying parameters
   - Test plugin fallback scenarios
   - Test with large number of plugins
   - Test circuit breaker interaction with NRDB

4. **zcp_rollout**
   - Test all backend implementations
   - Test parallel execution and throttling
   - Test error handling and recovery strategies
   - Test parallel execution with various thread counts
   - Test timeout handling
   - Test partial success scenarios

### Phase 2: Integration Test Expansion (Week 2)

Add comprehensive integration tests for key workflows:

1. **Error Recovery Workflow**
   - Test how the system handles failures at each stage
   - Verify proper error reporting and logging
   - Test retry mechanisms

2. **Performance Testing**
   - Test with simulated large host sets (1,000+ hosts)
   - Measure execution time and resource usage
   - Identify bottlenecks in the processing pipeline

3. **Edge Case Workflow**
   - Test with extreme parameters (very large templates, complex filters)
   - Test with slow or intermittent external services
   - Test with invalid or malformed inputs at each stage

### Phase 3: Operational Components (Week 3)

1. **zcp_validate**
   - Test threshold calculations
   - Test with various NRDB response formats
   - Test error handling in validation
   - Test multiple host validation

2. **zcp_lint**
   - Complete rule set tests
   - Test rule filtering
   - Test with complex YAML structures
   - Test edge cases in rules

3. **zcp_logging**
   - Test JSON formatting
   - Test context binding and propagation
   - Test span creation and timing
   - Test OTLP integration

4. **zcp_preset**
   - Test overlay mechanism
   - Test loading from multiple directories
   - Test SHA-256 verification
   - Test invalid preset handling

### Phase 4: Test Infrastructure Improvements (Week 4)

Enhance the testing framework and utilities:

1. **Test Fixtures**
   - Create comprehensive set of test fixtures for all components
   - Develop standardized mock implementations for external services
   - Create test data generators for various scenarios

2. **Coverage Reporting**
   - Implement automated coverage reporting in CI
   - Add coverage badges to README
   - Configure coverage thresholds for CI builds

3. **Test Documentation**
   - Document test patterns and best practices
   - Create testing guide for new contributors
   - Document test fixtures and how to use them

## Test Implementation Priorities

### Immediate Focus: High-Priority Unit Tests

Start with implementing tests for these specific components:

1. **zcp_core.bus**
   - Async backend error handling
   - Message ordering guarantees
   - Event filtering and routing

2. **zcp_cost.coordinator**
   - Plugin selection logic
   - Confidence threshold handling
   - Plugin result blending

3. **zcp_rollout.orchestrator**
   - Parallel execution control
   - Error handling during deployment
   - Progress reporting accuracy

### Integration Testing Roadmap

Implement these integration tests in order:

1. **Basic Wizard Flow**: Already implemented
2. **Error Recovery Flow**: Test system recovery from failures
3. **Large-Scale Deployment**: Test performance with many hosts
4. **Configuration Validation**: Test complete validation workflow
5. **Security Scenario**: Test handling of secure credentials and keys

## Phase 5: Performance Testing (Week 5)

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

### Test Performance Optimization

To support testing with large datasets and many test cases:

1. **Test Parallelization**
   - Configure pytest to run tests in parallel
   - Isolate tests that cannot run concurrently

2. **Resource Management**
   - Implement resource cleanup in fixtures
   - Add timeouts for long-running tests

### Continuous Integration

Enhance CI workflow to:

1. **Run Test Matrix**
   - Test across multiple Python versions
   - Test on multiple operating systems

2. **Quality Gates**
   - Block PRs that decrease coverage
   - Enforce test documentation

3. **Scheduled Tests**
   - Run full test suite nightly
   - Run performance tests weekly

## Success Criteria

The test improvement initiative will be considered successful when:

1. Overall test coverage exceeds 80%
2. All critical paths have dedicated tests
3. Integration tests cover all key workflows
4. Performance tests verify scalability requirements
5. All new features include comprehensive tests

## Timeline and Milestones

| Milestone | Target Date | Success Criteria |
|-----------|-------------|------------------|
| Phase 1 Completion | May 9, 2025 | Core components reach 75%+ coverage |
| Phase 2 Completion | May 16, 2025 | 5+ integration tests implemented |
| Phase 3 Completion | May 23, 2025 | Operational components fully tested |
| Phase 4 Completion | May 30, 2025 | Test infrastructure fully operational |
| Phase 5 Completion | June 6, 2025 | Performance testing completed |
| Final Coverage Goal | June 13, 2025 | 80%+ overall coverage achieved |

## Continuous Improvement

- Weekly test review meetings
- Test improvement tickets added to each sprint
- Test maintenance rotation among team members
- Quarterly test strategy review
