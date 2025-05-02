.PHONY: up down logs validate validate-json validate-detailed clean help docker-stats secure-off minimal \
        baseline lab-baseline lab-opt rate-sweep filter-matrix otel-study event-size \
        load-light load-heavy load-io visualize

# Original targets
up:          ## Launch the lab
	docker compose up -d --profile default

minimal:     ## Launch with minimal mounts (proc & sys only)
	docker compose -f docker-compose.yml -f overrides/min-mounts.yml up -d

docker-stats: ## Launch with Docker socket for container metrics
	docker compose up -d --profile docker-stats

secure-off:  ## Launch with seccomp disabled
	SECURE_MODE=false docker compose up -d

down:        ## Stop the lab
	docker compose down

logs:        ## Tail logs
	docker compose logs -f

validate:    ## Check ingestion stats
	./scripts/validate_ingest.sh

validate-detailed: ## Detailed validation with process breakdown
	./scripts/validate_ingest.sh --detailed

validate-json: ## Output validation in JSON format
	OUTPUT_JSON=true ./scripts/validate_ingest.sh

clean:       ## Remove all containers and volumes
	docker compose down -v

smoke:       ## Run local smoke test (same as CI)
	./scripts/ci_smoke.sh

# New targets for scenario testing

# Category 1: Baseline & Core-Opt
baseline:    ## Run baseline test (bare agent, no OTel)
	SCEN=A-0 PROFILE=bare-agent SAMPLE=20 ./scripts/run_one.sh

lab-baseline: ## Run lab baseline (default profiles)
	SCEN=A-1 PROFILE=default SAMPLE=20 ./scripts/run_one.sh

lab-opt:     ## Run optimized lab config
	SCEN=A-2 PROFILE=default SAMPLE=60 FILTER=yes ./scripts/run_one.sh

# Category 2: Sample-Rate Sweep
rate-sweep:  ## Run tests with different sample rates (20/30/60/90/120s)
	for r in 20 30 60 90 120; do \
	  SCEN=R-$${r} PROFILE=default SAMPLE=$${r} ./scripts/run_one.sh ; \
	done

# Category 3: Filtering Matrix
filter-matrix: ## Run tests with different filtering configurations
	SCEN=F-none PROFILE=default SAMPLE=60 FILTER=no ./scripts/run_one.sh
	SCEN=F-current PROFILE=default SAMPLE=60 docker compose -f docker-compose.yml -f overrides/filters/current.yml up -d
	sleep 1800 && OUTPUT_JSON=true ./scripts/validate_ingest.sh > results/$$(date +%Y%m%d_%H%M%S)/F-current.json && docker compose down
	SCEN=F-aggressive PROFILE=default SAMPLE=60 docker compose -f docker-compose.yml -f overrides/filters/aggressive.yml up -d
	sleep 1800 && OUTPUT_JSON=true ./scripts/validate_ingest.sh > results/$$(date +%Y%m%d_%H%M%S)/F-aggressive.json && docker compose down
	SCEN=F-targeted PROFILE=default SAMPLE=60 docker compose -f docker-compose.yml -f overrides/filters/targeted.yml up -d
	sleep 1800 && OUTPUT_JSON=true ./scripts/validate_ingest.sh > results/$$(date +%Y%m%d_%H%M%S)/F-targeted.json && docker compose down

# Category 4: OTel Contribution Study
otel-study:  ## Run tests analyzing OTel impact
	SCEN=M-0 PROFILE=bare-agent SAMPLE=60 ./scripts/run_one.sh
	SCEN=M-5 PROFILE=default SAMPLE=60 docker compose -f docker-compose.yml -f docker-compose.override.yml -v ./config/otel-5s.yaml:/etc/otel-config.yaml:ro up -d
	sleep 1800 && OUTPUT_JSON=true ./scripts/validate_ingest.sh > results/$$(date +%Y%m%d_%H%M%S)/M-5.json && docker compose down
	SCEN=M-10 PROFILE=default SAMPLE=60 ./scripts/run_one.sh
	SCEN=M-20 PROFILE=default SAMPLE=60 docker compose -f docker-compose.yml -f docker-compose.override.yml -v ./config/otel-20s.yaml:/etc/otel-config.yaml:ro up -d
	sleep 1800 && OUTPUT_JSON=true ./scripts/validate_ingest.sh > results/$$(date +%Y%m%d_%H%M%S)/M-20.json && docker compose down
	SCEN=M-scr-lite PROFILE=default SAMPLE=60 docker compose -f docker-compose.yml -f docker-compose.override.yml -v ./config/otel-scr-lite.yaml:/etc/otel-config.yaml:ro up -d
	sleep 1800 && OUTPUT_JSON=true ./scripts/validate_ingest.sh > results/$$(date +%Y%m%d_%H%M%S)/M-scr-lite.json && docker compose down
	SCEN=M-docker PROFILE=docker-stats SAMPLE=60 ./scripts/run_one.sh

# Category 5: Event Size Impact
event-size:  ## Run tests with different command line options
	SCEN=C-off PROFILE=default SAMPLE=60 ./scripts/run_one.sh
	SCEN=C-on PROFILE=default SAMPLE=60 COLLECT_CMDLINE=true ./scripts/run_one.sh
	SCEN=C-strip PROFILE=default SAMPLE=60 COLLECT_CMDLINE=true STRIP_CMDLINE=true ./scripts/run_one.sh

# Category 6: Load Robustness
load-light:  ## Run with light load (1 CPU, 64M memory)
	SCEN=L-light PROFILE=default SAMPLE=60 STRESS_CPU=1 STRESS_MEM=64M ./scripts/run_one.sh

load-heavy:  ## Run with heavy load (8 CPU, 1G memory)
	SCEN=L-heavy PROFILE=default SAMPLE=60 STRESS_CPU=8 STRESS_MEM=1G ./scripts/run_one.sh

load-io:     ## Run with IO-focused load
	SCEN=L-io PROFILE=default SAMPLE=60 LOAD_STRESSOR="--hdd 1" ./scripts/run_one.sh

# Visualization
visualize:   ## Generate result visualizations
	python3 ./scripts/generate_visualization.py

help:        ## Show this help
	@grep -E '^[a-zA-Z_-]+:.*?## .*$$' $(MAKEFILE_LIST) | awk 'BEGIN {FS = ":.*?## "}; {printf "\033[36m%-20s\033[0m %s\n", $$1, $$2}'

# Enable tab completion
.DEFAULT_GOAL := help