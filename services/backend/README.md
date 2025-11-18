# Backend service

FastAPI-based backend exposing `/api/v1` endpoints for the multi-tenant mini CRM. The service is intentionally structured by layers and domains to simplify future extraction into separate microservices.

## Layout

```
services/backend
├── Dockerfile
├── pyproject.toml
├── .env.example
├── alembic.ini
├── migrations/
├── src/mini_crm/
│   ├── app/            # FastAPI entrypoints & routers
│   ├── config/         # Settings, logging
│   ├── core/           # infrastructure helpers (db, security, pagination)
│   ├── shared/         # enums, DTO base objects
│   └── modules/        # domain modules (auth, organizations, ...)
└── tests/
```

## Workflow (Docker-only)

- `make up` / `make down` – поднять/остановить dev-стек (backend + postgres + redis).
- `make tests` – тестовый стек через `infra/docker-compose.test.yml`.
- `make lint`, `make format` – линтеры/типизация (ruff + mypy) и формат в `infra/Dockerfile.tools`.
- `make migrate`, `make makemigration name=msg` – работа с Alembic.

Все команды запускаются внутри контейнеров; локальные `poetry install`, `pytest`, `ruff` и т.п. не используются.
