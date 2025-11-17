# syntax=docker/dockerfile:1.6
FROM python:3.11-slim AS base

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    POETRY_HOME=/opt/poetry \
    POETRY_VERSION=1.8.2 \
    PATH="/opt/poetry/bin:$PATH"

RUN apt-get update \
    && apt-get install -y --no-install-recommends build-essential libpq-dev curl \
    && curl -sSL https://install.python-poetry.org | python3 - \
    && apt-get clean \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /app

FROM base AS deps
COPY pyproject.toml ./
# Copy lock file if it exists
RUN test -f poetry.lock && cp poetry.lock /app/ || true
RUN poetry config virtualenvs.create false \
    && poetry install --no-interaction --no-ansi

FROM deps AS builder
COPY . .
RUN poetry install --no-interaction --no-ansi

FROM base AS runtime
ENV PYTHONPATH=/app/src
COPY --from=builder /usr/local /usr/local
COPY --from=builder /app /app
EXPOSE 8000
CMD ["uvicorn", "mini_crm.app.main:app", "--host", "0.0.0.0", "--port", "8000"]

FROM builder AS lint-test
CMD ["bash", "-lc", "pytest"]
