# Infra-Lab Implementation Plan

## Project Overview
This implementation plan covers the development of Infra-Lab "Edge + NRDB Turbo," a toolkit for SREs to optimize ProcessSample configurations using New Relic Infrastructure Agent and NRDB. Key features include interactive guidance, noise analytics, dual-layer cost modeling, risk scoring, and fleet-wide rollout helpers.

## Phase 1: Testing Framework Setup

### 1.1 Test Infrastructure & Tools
- [ ] Set up tox configuration with all test environments
- [ ] Configure static analysis tools (ruff, mypy, bandit)
- [ ] Set up pytest with required plugins (snapshot, benchmark, hypothesis)
- [ ] Implement test repository structure according to layers
- [ ] Configure GitHub Actions CI pipeline for test matrix
- [ ] Set up code coverage reporting with minimum threshold of 90%
- [ ] Configure mutation testing with cosmic-ray
- [ ] Implement PR comment bot for test feedback

### 1.2 Static Testing
- [ ] Configure ruff linting with strict rules
- [ ] Set up mypy with strict typing enforcement
- [ ] Implement bandit security scanning
- [ ] Create pre-commit hooks for immediate feedback

### 1.3 Unit & Property Test Templates
- [ ] Create base test classes for each component
- [ ] Implement fixture factory for standard test cases
- [ ] Set up property-based test generators with hypothesis
- [ ] Create snapshot directories and baseline expected outputs
- [ ] Implement contract tests with JSON schema validation

### 1.4 Integration & System Test Environment
- [ ] Set up docker-compose test environment
- [ ] Configure pytest-docker for integration tests
- [ ] Create test harnesses for end-to-end validation
- [ ] Implement performance benchmarking baseline tests
- [ ] Configure fuzzing framework for CLI and config inputs

## Phase 2: Project Setup

### 2.1 Repository & Environment Setup
- [ ] Create project repository with structure as defined in section 4
- [ ] Configure CI/CD pipeline (pytest, yamllint, flake8)
- [ ] Set up development environments with Docker
- [ ] Create initial pyproject.toml with dependencies
- [ ] Establish branch protection rules

### 2.2 Project Planning & Documentation
- [ ] Finalize implementation schedule and resource allocation
- [ ] Conduct kickoff meeting with stakeholders
- [ ] Create detailed API design documents
- [ ] Set up project tracking board

## Phase 3: Core Modules Development

### 3.1 NRDB Integration
- [ ] Implement GraphQL client (src/process_lab/nrdb/client.py)
- [ ] Build queries interface (src/process_lab/nrdb/queries.py)
- [ ] Create mock responses for testing
- [ ] Implement cursor-based paging for large histograms
- [ ] Add support for GraphQL rate limit handling
- [ ] **Write contract tests for GraphQL schema validation**
- [ ] **Implement unit tests for client functionality**
- [ ] **Add property tests for pagination and error handling**

### 3.2 Cost Model Implementation
- [ ] Develop static heuristic model (src/process_lab/cost/static.py)
- [ ] Implement NRDB histogram model (src/process_lab/cost/histogram.py)
- [ ] Create blending model (src/process_lab/cost/blend.py)
- [ ] **Write property tests for cost model invariants**
- [ ] **Create unit tests with edge cases**
- [ ] **Add snapshot tests for expected outputs**
- [ ] Implement confidence calculation based on IQR
- [ ] **Write performance benchmarks for cost model**

### 3.3 Configuration Generator
- [ ] Develop Jinja2 templates for config generation
- [ ] Implement config_gen.py with template rendering
- [ ] Create templates for 8 workload archetypes
- [ ] Add validation for generated configs
- [ ] Implement preset system with override capabilities
- [ ] **Add snapshot tests for generated YAML**
- [ ] **Implement unit tests for template rendering**
- [ ] **Create property tests for template combinations**

## Phase 4: Validation & User Interaction

### 4.1 Linter & Risk Scoring
- [ ] Implement YAML schema validation
- [ ] Build risk heuristics with weighted rules
- [ ] Add pattern overlap detection (R4)
- [ ] Create SARIF output format
- [ ] Implement Tier-1 coverage simulation (R1)
- [ ] **Write unit tests for each risk rule**
- [ ] **Add snapshot tests for SARIF output**
- [ ] **Create property tests for risk score calculation**

### 4.2 Wizard Module
- [ ] Build interactive CLI with Typer
- [ ] Implement account & region detection
- [ ] Create slider UI for sample rate adjustment
- [ ] Integrate cost model for live predictions
- [ ] Add risk validation blocks
- [ ] Implement preset selection interface
- [ ] **Write integration tests with CliRunner**
- [ ] **Add snapshot tests for CLI output**
- [ ] **Create unit tests for wizard logic**

## Phase 5: Deployment & Telemetry

### 5.1 Roll-out Helper
- [ ] Implement SSH deployment mode
- [ ] Create Ansible integration
- [ ] Add command printing mode
- [ ] Implement backup & validation features
- [ ] Test idempotency of deployment
- [ ] Add force flag for high-risk deployments
- [ ] **Write unit tests for command generation**
- [ ] **Create integration tests with mock SSH server**
- [ ] **Add snapshot tests for generated commands**

### 5.2 Observability Implementation
- [ ] Set up OTLP export functionality
- [ ] Implement SQLite fallback storage
- [ ] Add key metrics collection
- [ ] Create visualizations for telemetry data
- [ ] Implement API key security measures
- [ ] **Write unit tests for telemetry collection**
- [ ] **Add property tests for database schema**
- [ ] **Create integration tests for metrics export**

## Phase 6: Integration & System Testing

### 6.1 End-to-End Test Suite
- [ ] Implement docker-compose integration tests
- [ ] Create full workflow test scenarios
- [ ] Implement golden test fixtures
- [ ] Build CI performance benchmark suite
- [ ] Implement fuzz testing for CLI input
- [ ] Create mutation testing configuration

### 6.2 System Validation
- [ ] Execute all acceptance tests (AT-01 through AT-05)
- [ ] Run load tests with sample data
- [ ] Conduct user acceptance testing
- [ ] Address packaging strategy (Open Question #3)
- [ ] Implement Cost-accuracy Golden Test
- [ ] Run full mutation test suite and fix survivors

## Phase 7: Documentation & Release

### 7.1 Documentation
- [ ] Complete user guide documentation
- [ ] Create wizard tutorial
- [ ] Write up architecture documentation
- [ ] Compile FAQ from testing feedback
- [ ] Document NRQL snippets and usage patterns
- [ ] Create test documentation and examples

### 7.2 Release Preparation
- [ ] Package for distribution (pipx vs system package)
- [ ] Create release notes
- [ ] Conduct final regression testing
- [ ] Prepare demo environments
- [ ] Implement dashboard JSON publication
- [ ] Verify test coverage meets 90% threshold

## Progress Tracking Table

| Component | Tasks Total | Tasks Completed | Status | Key Blockers |
|-----------|-------------|----------------|--------|--------------|
| Testing Framework | 22 | 0 | Not Started | - |
| Project Setup | 9 | 0 | Not Started | - |
| NRDB Integration | 8 | 0 | Not Started | - |
| Cost Model | 8 | 0 | Not Started | - |
| Config Generator | 8 | 0 | Not Started | - |
| Linter & Risk | 8 | 0 | Not Started | - |
| Wizard Module | 9 | 0 | Not Started | - |
| Roll-out Helper | 9 | 0 | Not Started | - |
| Observability | 8 | 0 | Not Started | - |
| End-to-End Testing | 6 | 0 | Not Started | - |
| System Validation | 6 | 0 | Not Started | - |
| Documentation | 6 | 0 | Not Started | - |
| Release Prep | 6 | 0 | Not Started | - |

## Test Coverage Goals

| Test Type | Target Coverage | Tools |
|-----------|----------------|-------|
| Unit Tests | 90% | pytest, pytest-cov |
| Property Tests | Critical functions | hypothesis |
| Snapshot Tests | All outputs | pytest-snapshot |
| Contract Tests | All API interactions | jsonschema |
| Integration Tests | All workflows | pytest-docker |
| Mutation Score | <10% survivors | cosmic-ray |
| Performance | Within budget | pytest-benchmark |

## Risk Register

| Risk | Impact | Probability | Mitigation |
|------|--------|------------|------------|
| GraphQL API changes | High | Low | Create abstraction layer; maintain fixtures for testing |
| GraphQL 500 rows limit | Medium | Medium | Implement cursor-based paging; sample top 500 PIDs |
| Over-filtering hides emerging Tier-1 processes | High | Medium | Enforce Tier-1 regex override; implement strong risk detection |
| Cost model drifts in spiky hosts | Medium | Low | Auto-reduce blend weight when confidence <0.6 |
| NR API rate-limits in large fleets | Low | Low | Implement local caching; add back-off for 429 responses |
| Cross-platform compatibility | Medium | Medium | Test on all target platforms; use Docker for consistency |
| Test suite performance in CI | Medium | Medium | Optimize test selection; use parallelization |

## Decision Log

| Date | Decision | Rationale | Alternatives Considered |
|------|----------|-----------|-------------------------|
| TBD | Testing framework | Comprehensive testing upfront to ensure quality | Traditional test-after approach |
| TBD | Risk score threshold | Will set at 7 based on spec | Considered dynamic thresholds |
| TBD | Packaging approach | To be decided (Open Question #3) | pipx vs system package |
| TBD | Telemetry storage | To be decided with packaging approach | Local vs central collection |
| TBD | Dashboard distribution | To be decided (Open Question #1) | JSON push vs NR pack |
| TBD | License key handling | To be decided (Open Question #2) | Environment detection vs prompt |
