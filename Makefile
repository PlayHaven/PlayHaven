.PHONY: help dev prod down logs shell db-shell clean test

# Variables
DC_DEV=docker-compose -f docker/docker-compose.dev.yml
DC_PROD=docker-compose -f docker/docker-compose.prod.yml

help: ## Show this help
	@grep -E '^[a-zA-Z_-]+:.*?## .*$$' $(MAKEFILE_LIST) | sort | awk 'BEGIN {FS = ":.*?## "}; {printf "\033[36m%-30s\033[0m %s\n", $$1, $$2}'

dev: ## Start development environment
	$(DC_DEV) build
	$(DC_DEV) up -d

prod: ## Start production environment
	$(DC_PROD) build
	$(DC_PROD) up -d

stop: ## Stop containers
	$(DC_DEV) down
	$(DC_PROD) down

logs-dev: ## View development logs
	$(DC_DEV) logs -f

logs-prod: ## View production logs
	$(DC_PROD) logs -f

shell-dev: ## Open a shell in the development web container
	$(DC_DEV) exec web /bin/bash

shell-prod: ## Open a shell in the production web container
	$(DC_PROD) exec web /bin/bash

db-shell: ## Open a psql shell in the database container
	$(DC_DEV) exec db psql -U postgres playhaven

clean: down ## Stop containers and remove volumes
	$(DC_DEV) down -v
	$(DC_PROD) down -v

test: ## Run tests
	$(DC_DEV) exec web python -m pytest

init-db: ## Initialize the database
	$(DC_DEV) exec web flask db init
	$(DC_DEV) exec web flask db migrate
	$(DC_DEV) exec web flask db upgrade

migrate-db: ## Migrate the database
	$(DC_DEV) exec web flask db migrate
	$(DC_DEV) exec web flask db upgrade

upgrade-db: ## Upgrade the database
	$(DC_DEV) exec web flask db upgrade

rollback-db: ## Rollback the database
	$(DC_DEV) exec web flask db downgrade

restart-dev: ## Restart development containers
	$(DC_DEV) down
	$(DC_DEV) up -d

restart-prod: ## Restart production containers
	$(DC_PROD) down
	$(DC_PROD) up -d

status: ## Show status of containers
	$(DC_DEV) ps
	$(DC_PROD) ps 