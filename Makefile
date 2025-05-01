.PHONY: up down logs validate validate-json validate-detailed clean help docker-stats secure-off minimal

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

help:        ## Show this help
	@grep -E '^[a-zA-Z_-]+:.*?## .*$$' $(MAKEFILE_LIST) | awk 'BEGIN {FS = ":.*?## "}; {printf "\033[36m%-20s\033[0m %s\n", $$1, $$2}'

# Enable tab completion
.DEFAULT_GOAL := help