# Lab Scenarios

The ProcessSample Optimization Lab supports various test scenarios to demonstrate optimization strategies and validate future capabilities.

## Core Scenarios

### Standard Optimization

**Purpose**: Demonstrate basic cost optimization with 60s sampling and process filtering

**Configuration**: Default setup with 60s sample rate and process filtering

```bash
make up
```

**Expected Outcomes**:
- ~70% reduction in ProcessSample ingest
- Full system visibility maintained

### Container Metrics Integration

**Purpose**: Combine host and container metrics for comprehensive visibility

**Configuration**: Adds Docker socket mount and docker_stats receiver

```bash
make docker-stats
```

**Benefits**:
- Container-level metrics alongside host metrics
- Correlation between container and process activity

## Advanced Test Scenarios

These scenarios help validate components of our strategic roadmap:

### 1. Dynamic Process Filtering (AS-1)

Adaptive filtering based on process importance and behavior patterns.

**Expected Outcome**: 80%+ ingest reduction with zero critical signal loss

### 2. Unified Dashboard (AS-2)

Comprehensive view of host and container metrics in a single dashboard.

**Expected Outcome**: Fast-loading dashboard (p95 load ≤ 100 ms)

### 3. Cost Attribution (AS-3)

Attribute monitoring costs to specific services, teams, or applications.

**Expected Outcome**: 90%+ cost attribution accuracy

### 4. Auto-Scaling Optimization (AS-4)

Use process data to optimize cloud resource allocation.

**Expected Outcome**: 20%+ reduction in idle CPU

### 5. Anomaly Detection (AS-5)

Identify unusual process behavior before it impacts service.

**Expected Outcome**: Low false positive rate (<2%) with high true positive rate (>70%)

## Future Test Scenarios

Additional scenarios planned as part of our roadmap:

1. **GitOps Configuration Management**: Version-controlled configuration with automated deployment
2. **Custom OpenTelemetry Metrics**: Extended metrics collection for specialized use cases
3. **Cross-Environment Comparison**: Analyze metrics across dev, test, and production
4. **Process Lifecycle Analysis**: Study process creation, runtime, and termination patterns
5. **Real-time Optimization Feedback Loop**: Continuous optimization based on actual usage

## Scenario Comparison Matrix

| Scenario | Focus Area | Key Metric | Value Proposition |
|----------|------------|------------|-------------------|
| Standard | Cost Reduction | Ingest Volume | 70% cost savings |
| Docker-Stats | Visibility | Container Correlation | Unified monitoring |
| Dynamic Filtering | Advanced Cost Reduction | Signal-to-Noise | 80%+ savings with integrity |
| Unified Dashboard | UX & Troubleshooting | Query Speed | Faster incident resolution |
| Cost Attribution | FinOps | Attribution Accuracy | Fair cost allocation |
| Auto-Scaling | Infrastructure Efficiency | Resource Utilization | Cloud cost optimization |
| Anomaly Detection | Proactive Monitoring | Prediction Accuracy | Early issue detection |