.PHONY: help build up down logs shell db-shell clean test

# Variables
DC=docker-compose -f docker/docker-compose.yml

help: ## Show this help
	@grep -E '^[a-zA-Z_-]+:.*?## .*$$' $(MAKEFILE_LIST) | sort | awk 'BEGIN {FS = ":.*?## "}; {printf "\033[36m%-30s\033[0m %s\n", $$1, $$2}'

start: ## Start the containers
	$(DC) build
	$(DC) up -d

stop: ## Stop the containers
	$(DC) down

logs: ## View logs
	$(DC) logs -f

shell: ## Open a shell in the web container
	$(DC) exec web /bin/bash

db-shell: ## Open a psql shell in the database container
	$(DC) exec db psql -U postgres playhaven

clean: down ## Stop containers and remove volumes
	$(DC) down -v

test: ## Run tests
	$(DC) exec web python -m pytest

init-db: ## Initialize the database
	$(DC) exec web flask db init
	$(DC) exec web flask db migrate
	$(DC) exec web flask db upgrade

migrate-db: ## Migrate the database
	$(DC) exec web flask db migrate
	$(DC) exec web flask db upgrade

upgrade-db: ## Upgrade the database
	$(DC) exec web flask db upgrade

rollback-db: ## Rollback the database
	$(DC) exec web flask db downgrade

restart: down up ## Restart the containers

status: ## Show status of containers
	$(DC) ps 