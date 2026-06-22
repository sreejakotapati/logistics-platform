# Logistics Management Platform — developer commands
.DEFAULT_GOAL := help
COMPOSE := docker compose

help: ## Show available commands
	@grep -E '^[a-zA-Z_-]+:.*?## ' $(MAKEFILE_LIST) | awk 'BEGIN{FS=":.*?## "}{printf "  \033[36m%-14s\033[0m %s\n", $$1, $$2}'

env: ## Create .env from .env.example if missing
	@test -f .env || (cp .env.example .env && echo "Created .env from .env.example — fill in values before starting")

up: env ## Start the full stack (backend/frontend require S1-T5/S1-T6)
	$(COMPOSE) up -d

up-infra: env ## Start only postgres + redis (works today)
	$(COMPOSE) up -d postgres redis

up-dev: env ## Start full stack + dev tools (mailhog, minio)
	$(COMPOSE) --profile dev up -d

down: ## Stop the stack (keep data)
	$(COMPOSE) down

reset: ## Stop and REMOVE volumes (wipes postgres/redis data)
	$(COMPOSE) down -v

build: ## Build backend & frontend images
	$(COMPOSE) build

logs: ## Tail logs (all services)
	$(COMPOSE) logs -f

ps: ## Show service status
	$(COMPOSE) ps

psql: ## Open a psql shell
	$(COMPOSE) exec postgres psql -U $${POSTGRES_USER:-app_user} -d $${POSTGRES_DB:-logistics}

redis-cli: ## Open redis-cli
	$(COMPOSE) exec redis redis-cli

sh-backend: ## Shell into the backend container
	$(COMPOSE) exec backend sh

sh-frontend: ## Shell into the frontend container
	$(COMPOSE) exec frontend sh

env-check: ## Validate required environment variables
	@bash scripts/check-env.sh

.PHONY: help env up up-infra up-dev down reset build logs ps psql redis-cli sh-backend sh-frontend env-check

# ---- Staging (cloud-agnostic) ----
staging-build: ## Build staging images
	docker compose -f docker-compose.staging.yml --env-file .env.staging build

staging-up: ## Start staging stack
	docker compose -f docker-compose.staging.yml --env-file .env.staging up -d

staging-down: ## Stop staging stack
	docker compose -f docker-compose.staging.yml --env-file .env.staging down

staging-deploy: ## Build + migrate + start + health-wait
	bash scripts/deploy-staging.sh

staging-logs: ## Tail staging logs
	docker compose -f docker-compose.staging.yml --env-file .env.staging logs -f

staging-backup: ## Run a Postgres backup
	bash scripts/backup-postgres.sh

monitoring-up: ## Start Prometheus + cAdvisor + node-exporter + Grafana
	docker compose -f docker-compose.monitoring.yml up -d

logging-up: ## Start Loki + Promtail
	docker compose -f docker-compose.logging.yml up -d
