# Contributing Guide

Thank you for your interest in contributing to the ProcessSample Optimization Lab. This document provides guidelines and best practices for contributors.

## Development Setup

1. Fork the repository
2. Clone your fork:
   ```bash
   git clone https://github.com/yourusername/infra-lab.git
   cd infra-lab
   ```
3. Create a branch for your changes:
   ```bash
   git checkout -b feature/your-feature-name
   ```

## Workflow

1. Make your changes
2. Test your changes locally:
   ```bash
   make smoke
   ```
3. Commit your changes with a descriptive message
4. Push your branch and create a pull request

## Version Bump Checklist

When updating container images or significant components:

1. Update the corresponding version numbers in:
   - `docker-compose.yml`
   - Technical documentation references
   - README.md badges and references

2. Run the smoke test to verify compatibility:
   ```bash
   make smoke
   ```

3. Update the CHANGELOG.md with details about the version change

4. For container image updates, consider:
   - Using SHA digests for immutability
   - Testing with multiple OS distributions if applicable
   - Verifying any API/configuration format changes

## Code Style

- Shell scripts: Follow [Google's Shell Style Guide](https://google.github.io/styleguide/shellguide.html)
- YAML: Use 2-space indentation
- Markdown: Use consistent heading levels and formatting

## Documentation

When updating documentation:

1. Keep code examples in sync with actual implementation
2. Update any version numbers consistently across all files
3. Validate links and references
4. Run mkdocs locally to preview changes:
   ```bash
   pip install mkdocs-material
   mkdocs serve
   ```

## Testing

- Add tests for new functionality
- Ensure existing tests pass
- For performance-critical changes, include benchmark results

## Pull Request Process

1. Ensure your PR addresses a specific issue or improvement
2. Include clear descriptions of changes
3. Update documentation as needed
4. Wait for CI to complete successfully
5. Address review feedback promptly

## License

By contributing, you agree that your contributions will be licensed under the project's MIT License.