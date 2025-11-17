COMPOSE ?= docker compose
DEV_COMPOSE := infra/docker-compose.dev.yml
TEST_COMPOSE := infra/docker-compose.test.yml
CI_COMPOSE := infra/docker-compose.ci.yml

.PHONY: help up down logs restart ps shell test tests lint typecheck format migrate makemigration

help:
	@echo "Available targets:"
	@echo "  make up        # Start dev stack"
	@echo "  make down      # Stop dev stack"
	@echo "  make logs      # Tail dev logs"
	@echo "  make tests     # Run backend test suite (docker only)"
	@echo "  make lint      # Run ruff lint"
	@echo "  make typecheck # Run mypy"
	@echo "  make format    # Auto-format via ruff"
	@echo "  make migrate   # Run Alembic migrations"
	@echo "  make makemigration name=msg # Autogenerate Alembic revision"

up:
	$(COMPOSE) -f $(DEV_COMPOSE) up --build -d

down:
	$(COMPOSE) -f $(DEV_COMPOSE) down --remove-orphans

logs:
	$(COMPOSE) -f $(DEV_COMPOSE) logs -f --tail=200 backend

restart: down up

ps:
	$(COMPOSE) -f $(DEV_COMPOSE) ps

shell:
	$(COMPOSE) -f $(DEV_COMPOSE) run --rm backend bash

test:
	@echo "Use 'make tests' to run the suite inside Docker." && exit 1

tests:
	$(COMPOSE) -f $(TEST_COMPOSE) run --rm backend-tests

lint:
	docker build -f infra/Dockerfile.tools -t test-kitchen-tools .
	docker run --rm -v $(PWD):/workspace test-kitchen-tools ruff check services

typecheck:
	docker build -f infra/Dockerfile.tools -t test-kitchen-tools .
	docker run --rm -v $(PWD):/workspace test-kitchen-tools mypy services/backend/src

format:
	docker build -f infra/Dockerfile.tools -t test-kitchen-tools .
	docker run --rm -v $(PWD):/workspace test-kitchen-tools sh -c "ruff format services && ruff check --fix services"

migrate:
	$(COMPOSE) -f $(DEV_COMPOSE) run --build --rm migrations alembic upgrade head

makemigration:
	@if [ -z "$(name)" ]; then echo "Usage: make makemigration name=short_description"; exit 1; fi
	$(COMPOSE) -f $(DEV_COMPOSE) run --build --rm migrations alembic revision --autogenerate -m "$(name)"
