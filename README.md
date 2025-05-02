# Infra-Lab: ProcessSample Optimization Toolkit 🚀

[![CI](https://github.com/deepaucksharma/infra-lab/actions/workflows/ci.yml/badge.svg)](./.github/workflows/ci.yml)
[![License](https://img.shields.io/badge/license-MIT-blue)](LICENSE)

A toolkit and local lab environment for discovering, predicting, generating, validating, and rolling out cost-optimized **New Relic ProcessSample** configurations using the New Relic Infrastructure Agent and NRDB analysis. Aim to reduce ingest costs significantly (targeting ≤ 1-2 GB/host/day) while preserving essential process visibility.

| 🔗 Docs Quick Start | 🔗 Full Specification | 🔗 CLI Help |
|--------------------|-----------------------|-------------|
| [Quick Start Guide](docs/quickstart.md) | [Technical Spec](docs/technical-specification.md) | `process-lab --help` |

---

## 1. The Challenge & Solution

ProcessSample events provide deep visibility but can be expensive due to high frequency (default 20s), high cardinality (per-process), and potentially large event size (with command lines). Turning them off saves cost but hurts observability.

Infra-Lab helps find the right balance:

*   **Analyze:** Uses NRDB data (if API key provided) to understand current process landscape.
*   **Model:** Employs static and dynamic models to predict cost/visibility impact of changes.
*   **Generate:** Creates Infrastructure Agent `newrelic-infra.yml` configurations based on templates, presets, or recommendations.
*   **Lint:** Checks configurations for potential risks (e.g., filtering critical processes).
*   **Recommend:** Suggests optimized configurations based on NRDB data and constraints.
*   **Rollout:** Generates artifacts (Ansible, scripts) for deploying configurations.
*   **(Local Lab):** Includes a Docker Compose setup (`compose/`) for *manually* testing generated configurations with a load generator and OTel collector.

---

## 2. Architecture

The core toolkit is a Python CLI application. It interacts with NRDB via the GraphQL API (for analysis and dynamic cost modeling) and generates static YAML configuration files for the New Relic Infrastructure Agent.

```mermaid
flowchart LR
    subgraph "User Machine"
        CLI["process-lab CLI Tool"]
    end

    subgraph "Target Host(s)"
        direction LR
        subgraph "Generated Artifacts"
            CFG["newrelic-infra.yml"]
        end
        subgraph "Agent"
             AGENT["NR Infrastructure Agent"]
        end
        CFG --> AGENT
    end

    subgraph "New Relic Platform"
        NR[(NRDB)]
        API[GraphQL API]
    end

    CLI -- Generate --> CFG
    CLI -- Analyze/Estimate --> API
    AGENT -- ProcessSample --> NR
    NR -- Data --> API

    style CLI fill:#cfe2f3,stroke:#333
    style AGENT fill:#d9ead3,stroke:#333
    style NR fill:#e4d1f4,stroke:#333
    style API fill:#e4d1f4,stroke:#333


(Note: The optional Docker environment in compose/ is for local testing and is not directly managed by the process-lab CLI commands like up/down.)

## 3. Core Goals

| ID  | Goal                                  | Target                                                        |
| --- | ------------------------------------- | ------------------------------------------------------------- |
| G1  | Reduce ProcessSample ingest           | ≤ 1-2 GB/day/host (typical ~70% reduction)                    |
| G2  | Preserve Tier-1 process visibility   | Critical processes remain unfiltered                            |
| G3  | Achieve ±10% cost estimate accuracy | vs. actual NrConsumption data                                 |
| G4  | Provide actionable CLI & templates    | Minimize manual YAML editing                                  |

(See Technical Specification for full details.)

## 4. Quick Start

See the detailed [Quick Start Guide](docs/quickstart.md).

## 5. Repository Map

```text
deepaucksharma-infra-lab/
├── README.md                 <- You are here
├── pyproject.toml            <- Build definition, dependencies, CLI entry point
├── tox.ini                   <- Test automation configuration
├── .env.example              <- Environment variable template (API keys etc.)
│
├── src/
│   └── process_lab/          <- Main package source code
│       ├── __init__.py
│       ├── cli/              <- Typer CLI application (app.py, commands.py)
│       ├── client/           <- API clients (nrdb.py)
│       ├── core/             <- Core logic (config.py, cost.py, analysis.py)
│       ├── models/           <- Cost models (static.py, dynamic.py, blended.py)
│       └── utils/            <- Utilities (lint.py, rollout.py, templates.py)
│
├── templates/                <- Source templates
│   ├── newrelic-infra.tpl.yaml   <- Agent config Jinja2 template
│   ├── filter-definitions.yml    <- Process filter pattern definitions
│   └── wizard-presets.yml        <- Pre-defined configuration presets
│
├── config/                   <- Default *output* location for generated configs
│   └── newrelic-infra.yml    <- Example/Default output file (overwritten by CLI!)
│
├── compose/                  <- Docker Compose environment for *manual* local testing
│   ├── docker-compose.yml
│   └── ...
│
├── nrdb_analysis/            <- Useful NRQL queries & dashboard JSON
│   ├── README.md
│   └── ...
│
├── tests/                    <- Pytest test suite (unit, integration, etc.)
└── docs/                     <- Documentation files (quickstart.md, faq.md, etc.)
```

## 6. Contributing

Development uses tox for testing and linting.

```bash
# Install for development (editable mode + dev dependencies)
pip install -e ".[dev]"

# Run all checks (linting, typing, tests)
tox -p auto

# Run specific tests
tox -e lint
tox -e unit
tox -e integration
```

We enforce Ruff, MyPy, high test coverage (via pytest-cov), and low mutation test survival rates (via cosmic-ray). Please see `tox.ini` for details.

MIT License © 2025 New Relic Inc.
