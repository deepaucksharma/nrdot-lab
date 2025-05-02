.PHONY: up down logs validate validate-json validate-csv clean help generate-configs \
        docker-stats secure-mode secure-off minimal filter-none filter-standard filter-aggressive filter-targeted \
        baseline lab-baseline lab-opt rate-sweep filter-matrix otel-study event-size \
        load-light load-heavy load-io visualize crossplatform

# Core commands
up:                ## Launch the lab with standard configuration
	docker compose up -d

down:              ## Stop the lab
	docker compose down

logs:              ## Tail logs
	docker compose logs -f

validate:          ## Check ingestion stats (text output)
	./scripts/validate.sh --format text

validate-json:     ## Output validation in JSON format
	./scripts/validate.sh --format json

validate-csv:      ## Output validation in CSV format
	./scripts/validate.sh --format csv

clean:             ## Remove all containers and volumes
	docker compose down -v

generate-configs:  ## Generate all configuration files from templates
	./scripts/generate_configs.sh

# Configuration variants
minimal:           ## Launch with minimal mounts (proc & sys only)
	MIN_MOUNTS= docker compose up -d

docker-stats:      ## Launch with Docker socket for container metrics
	ENABLE_DOCKER_STATS=true docker compose up -d

secure-mode:       ## Launch with seccomp enabled
	SECURE_MODE=true docker compose up -d

secure-off:        ## Launch with seccomp disabled
	SECURE_MODE= docker compose up -d

# Filter types
filter-none:       ## Use no process filtering
	FILTER_TYPE=none docker compose up -d

filter-standard:   ## Use standard process filtering
	FILTER_TYPE=standard docker compose up -d

filter-aggressive: ## Use aggressive process filtering
	FILTER_TYPE=aggressive docker compose up -d

filter-targeted:   ## Use targeted process filtering
	FILTER_TYPE=targeted docker compose up -d

# Sample rate settings
sample-20:         ## Use 20s sample rate (default NR)
	SAMPLE_RATE=20 docker compose up -d

sample-60:         ## Use 60s sample rate (recommended)
	SAMPLE_RATE=60 docker compose up -d

sample-120:        ## Use 120s sample rate (maximum savings)
	SAMPLE_RATE=120 docker compose up -d

# Testing scenarios
# Category 1: Baseline & Core-Opt
baseline:          ## Run baseline test (bare agent, no OTel)
	SCEN=A-0 PROFILE=bare-agent SAMPLE_RATE=20 ./scripts/run_one.sh

lab-baseline:      ## Run lab baseline (default profiles)
	SCEN=A-1 PROFILE=default SAMPLE_RATE=20 ./scripts/run_one.sh

lab-opt:           ## Run optimized lab config
	SCEN=A-2 PROFILE=default SAMPLE_RATE=60 FILTER_TYPE=standard ./scripts/run_one.sh

# Category 2: Sample-Rate Sweep
rate-sweep:        ## Run tests with different sample rates
	for r in 20 30 60 90 120; do \
	  SCEN=R-$${r} PROFILE=default SAMPLE_RATE=$${r} ./scripts/run_one.sh ; \
	done

# Category 3: Filtering Matrix
filter-matrix:     ## Run tests with different filtering configurations
	SCEN=F-none PROFILE=default SAMPLE_RATE=60 FILTER_TYPE=none ./scripts/run_one.sh
	SCEN=F-standard PROFILE=default SAMPLE_RATE=60 FILTER_TYPE=standard ./scripts/run_one.sh
	SCEN=F-aggressive PROFILE=default SAMPLE_RATE=60 FILTER_TYPE=aggressive ./scripts/run_one.sh
	SCEN=F-targeted PROFILE=default SAMPLE_RATE=60 FILTER_TYPE=targeted ./scripts/run_one.sh

# Category 4: OTel Contribution Study
otel-study:        ## Run tests analyzing OTel impact
	SCEN=M-0 PROFILE=bare-agent SAMPLE_RATE=60 ./scripts/run_one.sh
	SCEN=M-5 PROFILE=default SAMPLE_RATE=60 OTEL_INTERVAL=5s ./scripts/run_one.sh
	SCEN=M-10 PROFILE=default SAMPLE_RATE=60 OTEL_INTERVAL=10s ./scripts/run_one.sh
	SCEN=M-20 PROFILE=default SAMPLE_RATE=60 OTEL_INTERVAL=20s ./scripts/run_one.sh
	SCEN=M-docker PROFILE=default SAMPLE_RATE=60 ENABLE_DOCKER_STATS=true ./scripts/run_one.sh

# Category 5: Event Size Impact
event-size:        ## Run tests with different command line options
	SCEN=C-off PROFILE=default SAMPLE_RATE=60 COLLECT_CMDLINE=false ./scripts/run_one.sh
	SCEN=C-on PROFILE=default SAMPLE_RATE=60 COLLECT_CMDLINE=true ./scripts/run_one.sh

# Category 6: Load Robustness
load-light:        ## Run with light load (1 CPU, 64M memory)
	SCEN=L-light PROFILE=default SAMPLE_RATE=60 STRESS_CPU=1 STRESS_MEM=64M ./scripts/run_one.sh

load-heavy:        ## Run with heavy load (8 CPU, 1G memory)
	SCEN=L-heavy PROFILE=default SAMPLE_RATE=60 STRESS_CPU=8 STRESS_MEM=1G ./scripts/run_one.sh

load-io:           ## Run with IO-focused load
	SCEN=L-io PROFILE=default SAMPLE_RATE=60 STRESS_IO=2 ./scripts/run_one.sh

# Visualization
visualize:         ## Generate result visualizations
	python3 ./scripts/visualize.py

# Cross-platform support
crossplatform:     ## Run cross-platform compatibility setup
	@if [ -f /proc/version ]; then \
		echo "Detected Linux, using bash scripts"; \
		chmod +x ./scripts/*.sh; \
	else \
		echo "Detected Windows or macOS"; \
		if command -v powershell >/dev/null 2>&1; then \
			echo "Using PowerShell scripts"; \
			powershell -ExecutionPolicy Bypass -File ./scripts/setup.ps1; \
		fi; \
	fi

help:              ## Show this help
	@grep -E '^[a-zA-Z_-]+:.*?## .*$$' $(MAKEFILE_LIST) | sort | awk 'BEGIN {FS = ":.*?## "}; {printf "\033[36m%-20s\033[0m %s\n", $$1, $$2}'

# Enable tab completion
.DEFAULT_GOAL := help