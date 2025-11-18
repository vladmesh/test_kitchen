from contextlib import asynccontextmanager

from fastapi import FastAPI

from mini_crm.config.logging import configure_logging
from mini_crm.config.settings import get_settings
from mini_crm.core.cache import RedisCache
from mini_crm.modules.activities.api.router import router as activities_router
from mini_crm.modules.analytics.api.router import router as analytics_router
from mini_crm.modules.auth.api.router import router as auth_router
from mini_crm.modules.common.api.router import router as common_router
from mini_crm.modules.contacts.api.router import router as contacts_router
from mini_crm.modules.deals.api.router import router as deals_router
from mini_crm.modules.organizations.api.router import router as organizations_router
from mini_crm.modules.tasks.api.router import router as tasks_router


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Lifespan context manager for app startup and shutdown."""
    # Startup
    yield
    # Shutdown
    cache = RedisCache.get_instance()
    await cache.close()


def create_app() -> FastAPI:
    settings = get_settings()
    configure_logging(settings)

    app = FastAPI(
        title="Mini CRM API",
        version="0.1.0",
        docs_url="/docs",
        redoc_url="/redoc",
        debug=settings.api_debug,
        lifespan=lifespan,
    )

    app.include_router(common_router, prefix="/api")
    app.include_router(auth_router, prefix="/api/v1")
    app.include_router(organizations_router, prefix="/api/v1")
    app.include_router(contacts_router, prefix="/api/v1")
    app.include_router(deals_router, prefix="/api/v1")
    app.include_router(tasks_router, prefix="/api/v1")
    app.include_router(activities_router, prefix="/api/v1")
    app.include_router(analytics_router, prefix="/api/v1")

    return app


app = create_app()


@app.get("/health", tags=["system"])
async def healthcheck() -> dict[str, str]:
    """Internal liveness probe."""

    return {"status": "ok"}
