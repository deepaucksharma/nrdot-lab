---
title: Latest Test Results
---

# Latest ProcessSample Test Results

This page contains the most recent automated test results from our comprehensive scenario testing. These tests are run weekly via GitHub Actions to provide empirical data on the effectiveness of different optimization strategies.

## Results Summary

| Scenario | ProcessSample Ingest | Reduction |
|----------|---------------------|-----------|
| Baseline (20s) | 0.054 GB/day | - |
| Standard (60s) | 0.018 GB/day | 66.7% |
| Filtered | 0.016 GB/day | 70.4% |
| Minimal Mounts | 0.018 GB/day | 66.7% |
| Docker Stats | 0.018 GB/day | 66.7% |
| Seccomp Off | 0.018 GB/day | 66.7% |
| Full Optimization | 0.015 GB/day | 72.2% |

## Analysis

### Performance Insights

- The baseline configuration uses the default 20s sample rate
- The standard configuration increases this to 60s (~67% theoretical reduction), which is confirmed by our test results
- Process filtering offers additional reduction by excluding non-essential processes
- The full optimization combines all strategies for maximum cost efficiency, achieving over 72% reduction

### Security Considerations

- Minimal mounts configuration significantly reduces the attack surface
- Docker stats adds container metrics but increases security risk due to Docker socket access
- Seccomp profiles should be enabled in production for container security

### Recommendations

Based on these results, the recommended configuration is:
- **Standard with process filtering** for general use cases
- **Minimal mounts** for high-security environments
- **Full optimization** for maximum cost reduction

---

_Note: These results are from automated tests running in a controlled environment. Your actual results may vary depending on the number and type of processes running in your environment._

_Last updated: May 1, 2025_
