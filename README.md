# Mini-CRM Platform

Backend-first playground for a multi-tenant mini-CRM. The repo follows a microservice-friendly layout even though only the backend service is implemented for now.

## Repository layout

```
.
├── docs/               # SRE/dev notes, ADRs, swagger exports, etc.
├── infra/              # docker-compose, deployment manifests, shared infra scripts
├── services/
│   └── backend/        # FastAPI + PostgreSQL service
├── tests/              # Cross-service/e2e tests (future use)
├── README.md           # High-level overview
├── TZ.md               # Full assignment / product requirements
└── PLAN.md             # Implementation plan and roadmap
```

The `services/backend` directory contains everything related to the FastAPI service (source, tests, tool configs, Dockerfile, Poetry files, migrations, etc.). Additional services can be added alongside it without touching existing ones.

## Target architecture

- **API**: FastAPI, versioned under `/api/v1`.
- **Storage**: PostgreSQL + Alembic migrations, optional Redis for caching/queueing.
- **Auth**: JWT (access + refresh) with organization context header `X-Organization-Id`.
- **Quality gates**: ruff, mypy, pytest (async friendly) wired into Docker/Make targets.
- **Deployment**: Multi-stage Docker build artifacts, docker-compose stacks for dev/test/CI.

## Getting started

```bash
# Start dev stack (backend + Postgres + Redis) with hot reload
make up

# Stop everything
make down

# Run tests / lint / mypy inside Docker
make tests   # docker compose test stack
make lint
make typecheck
```

Detailed service-specific instructions live in `services/backend/README.md`.

## Roadmap

The work is tracked in `PLAN.md`. Major milestones:

1. Repository skeleton (this commit).
2. Backend service scaffolding (Poetry project, FastAPI layers, tests).
3. Infrastructure assets (Dockerfiles, compose stacks, Makefile shortcuts).
4. Business logic implementation per module (auth → organizations → contacts → deals → tasks → activities → analytics).
5. CI/CD + documentation polish.
