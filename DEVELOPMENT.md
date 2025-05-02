# ZCP Development Plan

This document outlines the development plan for ZCP, including upcoming tasks, priority, and implementation details.

## Current Status

The project has been bootstrapped with core components:
- Event bus with three backends (sync, async, trace)
- Schema registry with validation
- Preset management
- Template rendering
- Cost estimation
- Basic CLI interface

## Current Focus: Test Expansion

The current development priority is expanding and improving our test suite. This includes:

### 1. Unit Test Coverage

We aim to achieve 80%+ test coverage across all components:

```bash
# Check coverage across all components
hatch run coverage

# Check coverage for a specific component
hatch run coverage --project zcp_cost
```

#### Unit Test Priorities

1. **Critical Components**: Focus on bus, cost, and rollout modules
2. **Edge Cases**: Add tests for error handling and edge conditions
3. **Configuration Variations**: Test with various configuration settings

### 2. Integration Testing

We need to add integration tests that verify components work together:

```bash
# Run integration tests
hatch run integ
```

#### Integration Test Scenarios

- Complete wizard → render → cost → rollout → validate flow
- Error handling and recovery
- Performance under load (10k hosts simulation)

### 3. Test Fixtures and Utilities

To support testing, we need to develop:

- Common test fixtures for repeated test cases
- Mock services for external dependencies (NRDB, SSH, etc.)
- Test data generators for configurations and responses

### Testing Standards

- All PRs must maintain or increase test coverage
- Critical bug fixes must include regression tests
- New features must include tests for nominal and error paths
- Integration tests must be isolated and repeatable

## Development Workflow

1. **Feature Implementation**:
   - Create branch with format `feature/component-name`
   - Implement the feature with tests
   - Update documentation
   - Create PR for review

2. **Testing**:
   - Run unit tests with `hatch run test`
   - Check type safety with `hatch run typecheck`
   - Verify code style with `hatch run lint`

3. **Documentation**:
   - Update ADRs for architectural decisions
   - Document module interfaces and contracts
   - Update README with new features

## Component Details

### Rollout Module

The rollout module will handle deployment of configurations to hosts:

```python
# src/zcp_rollout/orchestrator.py
class RolloutOrchestrator:
    def execute(self, job: RolloutJob) -> RolloutReport:
        """Execute a rollout job."""
        # Implementation...

class RolloutJob(BaseModel):
    hosts: List[str]
    template: str
    parallel: int = 10
    timeout_s: int = 30
    
class RolloutReport(BaseModel):
    success: int
    fail: int
    duration_s: float
    details: Dict[str, str]
```

### Validation Module

The validation module will verify configurations are working correctly:

```python
# src/zcp_validate/validator.py
class Validator:
    def validate(self, job: ValidationJob) -> ValidationResult:
        """Validate configuration was applied correctly."""
        # Implementation...

class ValidationJob(BaseModel):
    hosts: List[str]
    expected_gib_day: float
    confidence: float
    
class ValidationResult(BaseModel):
    pass: bool
    actual_gib_day: float
```

## Progress Tracking

Update ROADMAP.md after completing each component with:
- Actual completion percentage
- Any modifications to the design
- Notes about challenges or future improvements

## Development Environment Setup

For new developers joining the project:

```bash
# Clone repository
git clone https://github.com/example/zcp.git
cd zcp

# Install development tools
pip install hatch

# Setup virtual environment
hatch shell

# Run tests
hatch run test
```

## Continuous Integration

The CI pipeline will run on each PR and include:
- Unit tests for all Python versions
- Type checking
- Linting
- Coverage reporting

See `.github/workflows/ci.yml` for details.
