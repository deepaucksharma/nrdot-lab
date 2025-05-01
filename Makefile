.PHONY: up down logs validate clean help smoke full-host docker-stats seccomp-off lint

SECCOMP_PROFILE ?= ./profiles/seccomp-nr.json

up:          ## Launch the lab with minimal-mounts (default)
	docker compose up -d --profile default

full-host:   ## Launch with full host filesystem mounts
	docker compose -f docker-compose.yml -f overrides/full-host.yml up -d

docker-stats: ## Launch with Docker socket for container metrics
	docker compose up -d --profile docker-stats

seccomp-off: ## Launch with security profile disabled
	SECURE_MODE= docker compose up -d

seccomp-v2:  ## Launch with enhanced seccomp profile
	SECCOMP_PROFILE=./profiles/seccomp-v2.json docker compose up -d

down:        ## Stop the lab
	docker compose down

logs:        ## Tail logs
	docker compose logs -f

validate:    ## Check ingestion stats
	./scripts/validate_ingest.sh

validate-detailed: ## Detailed validation with process breakdown
	./scripts/validate_ingest.sh --detailed

clean:       ## Remove all containers and volumes
	docker compose down -v

smoke:       ## Run local smoke test (same as CI)
	./scripts/ci_smoke.sh

lint:        ## Run linting on shell scripts
	shellcheck scripts/*.sh

help:        ## Show this help
	@grep -E '^[a-zA-Z_-]+:.*?## .*$$' $(MAKEFILE_LIST) | awk 'BEGIN {FS = ":.*?## "}; {printf "\033[36m%-20s\033[0m %s\n", $$1, $$2}'