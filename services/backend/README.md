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

## Run locally

```bash
# install poetry deps locally (optional, docker compose handles this too)
poetry install
poetry run uvicorn mini_crm.app.main:app --reload
```

Environment variables are configured through `.env.example`. Copy it to `.env` (or inject variables via docker-compose) before running.

## Developer commands

Most workflows are available via the repo-level `Makefile`:

- `make up` / `make down` – run the dockerized dev stack (backend + postgres + redis).
- `make test` – run pytest, ruff, mypy inside the lint-test stage.
- `make migrate` – execute Alembic migrations in the migrations container.

## Next steps

- Implement actual repositories/services inside each module.
- Flesh out migrations with the schema from `TZ.md`.
- Expand tests to cover multi-tenant and role-specific behaviour.
