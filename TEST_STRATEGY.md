# ZCP Testing Strategy

## Overview

This document outlines the testing strategy for the ZCP project. It covers different types of tests, priorities, and guidelines for test development.

## Testing Goals

1. **Quality Assurance**: Ensure the software works as expected and remains stable as it evolves
2. **Regression Prevention**: Prevent regressions when making changes
3. **Documentation**: Tests serve as executable documentation of expected behavior
4. **Edge Case Handling**: Verify correct behavior in unusual or extreme situations
5. **Performance Verification**: Ensure the system meets performance requirements

## Test Types

### Unit Tests

Unit tests focus on testing individual components in isolation.

#### Coverage Targets
- **Core modules (zcp_core, zcp_cost)**: 90%+
- **Operational modules**: 80%+
- **Utility modules**: 70%+

#### Key Areas to Test
- **Event Bus**: Test all backends and event routing
- **Schema Validation**: Test validation against schemas
- **Cost Estimation**: Test different plugins and blending
- **Template Rendering**: Test with different token types
- **Preset Loading**: Test overlay mechanism
- **Linting Rules**: Test each rule individually
- **Rollout Logic**: Test backend selection and parallel execution
- **Validation Logic**: Test threshold comparisons

### Integration Tests

Integration tests verify that components work together correctly.

#### Key Workflows to Test
- **Wizard to Rollout**: Complete workflow from wizard to deployment
- **Validation Cycle**: Rollout followed by validation
- **Config Generation**: Preset to template to linting
- **NRDB Integration**: Test interactions with external services

### Performance Tests

Performance tests verify system behavior under load.

#### Performance Benchmarks
- **10,000 Host Rollout**: < 7 minutes as per specification
- **Template Rendering**: < 100ms per template
- **Cost Estimation**: < 2s response time
- **Bus Throughput**: Handle 1,000 events/second with async backend

### Security Tests

Security tests verify that the system follows security best practices.

#### Security Areas
- **SSH Key Handling**: Verify proper key management
- **API Key Management**: Verify secure handling of API keys
- **Permission Checking**: Verify proper file permissions
- **Input Validation**: Verify all inputs are validated

## Test Implementation Priorities

1. **Critical Path Testing**: Focus on the main workflows first
2. **Error Handling**: Test failure modes and recovery paths
3. **Edge Cases**: Test boundary conditions and unusual inputs
4. **Performance**: Test with realistic load and scale

## Test Implementation Guidelines

### Test Structure

Follow a consistent test structure:
```python
def test_something():
    # Arrange - Set up test data and conditions
    ...
    
    # Act - Execute the functionality being tested
    ...
    
    # Assert - Verify expected outcomes
    ...
```

### Mocking Guidelines

- Mock external dependencies (NRDB, SSH, file system)
- Use fixture data for consistent testing
- Document mock behavior clearly

### Test Naming

Use descriptive test names that explain what's being tested:
```python
def test_cost_coordinator_blends_top_two_plugins_by_confidence():
    ...
```

## Test Fixtures and Utilities

### Common Fixtures
- Standard preset configurations
- Template examples
- YAML configurations (valid and invalid)
- Mock NRDB responses

### Utilities
- Event bus test helpers
- Configuration generators
- Mock backend implementations
- NRDB response simulators

## CI Integration

- All tests must pass before merging PRs
- Coverage reports generated for each PR
- Performance benchmarks run nightly
- Test failures block merges

## Test Maintenance

- Tests should be reviewed along with code changes
- Flaky tests should be fixed or marked for investigation
- Test data should be kept up to date with schema changes
- Documentation should be updated when test expectations change
