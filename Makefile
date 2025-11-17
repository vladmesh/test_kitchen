COMPOSE ?= docker compose
DEV_COMPOSE := infra/docker-compose.dev.yml
TEST_COMPOSE := infra/docker-compose.test.yml
CI_COMPOSE := infra/docker-compose.ci.yml

.PHONY: help up down logs restart ps shell test lint typecheck format migrate

help:
	@echo "Available targets:"
	@echo "  make up        # Start dev stack"
	@echo "  make down      # Stop dev stack"
	@echo "  make logs      # Tail dev logs"
	@echo "  make test      # Run backend test suite"
	@echo "  make lint      # Run ruff lint"
	@echo "  make typecheck # Run mypy"
	@echo "  make format    # Auto-format via ruff"
	@echo "  make migrate   # Run Alembic migrations"

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
	$(COMPOSE) -f $(TEST_COMPOSE) run --rm backend-tests

lint:
	$(COMPOSE) -f $(TEST_COMPOSE) run --rm backend-tests ruff check src

typecheck:
	$(COMPOSE) -f $(TEST_COMPOSE) run --rm backend-tests mypy src

format:
	$(COMPOSE) -f $(TEST_COMPOSE) run --rm backend-tests ruff format src

migrate:
	$(COMPOSE) -f $(DEV_COMPOSE) run --rm migrations alembic upgrade head
