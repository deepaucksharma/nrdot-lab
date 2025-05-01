.PHONY: up down logs validate clean help docker-stats

up:          ## Launch the lab
	docker compose up -d --profile default

docker-stats: ## Launch with Docker socket for container metrics
	docker compose up -d --profile docker-stats

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

help:        ## Show this help
	@grep -E '^[a-zA-Z_-]+:.*?## .*$$' $(MAKEFILE_LIST) | awk 'BEGIN {FS = ":.*?## "}; {printf "\033[36m%-20s\033[0m %s\n", $$1, $$2}'