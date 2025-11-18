from __future__ import annotations

import os
from collections.abc import AsyncGenerator

import pytest_asyncio
from httpx import ASGITransport, AsyncClient
from sqlalchemy.ext.asyncio import (
    AsyncEngine,
    AsyncSession,
    async_sessionmaker,
    create_async_engine,
)

from mini_crm.app.main import app
from mini_crm.core.cache import RedisCache
from mini_crm.core.db import Base
from mini_crm.core.dependencies import get_db_session
from mini_crm.modules.activities import models as activities_models  # noqa: F401
from mini_crm.modules.auth import models as auth_models  # noqa: F401
from mini_crm.modules.contacts import models as contacts_models  # noqa: F401
from mini_crm.modules.deals import models as deals_models  # noqa: F401
from mini_crm.modules.organizations import models as organizations_models  # noqa: F401
from mini_crm.modules.tasks import models as tasks_models  # noqa: F401


@pytest_asyncio.fixture
async def async_engine() -> AsyncGenerator[AsyncEngine, None]:
    database_url = os.getenv("DATABASE_URL")
    if not database_url:
        raise ValueError("DATABASE_URL environment variable must be set")

    engine = create_async_engine(database_url, future=True)

    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.drop_all)
        await conn.run_sync(Base.metadata.create_all)
    yield engine
    await engine.dispose()


@pytest_asyncio.fixture
async def session_factory(
    async_engine: AsyncEngine,
) -> AsyncGenerator[async_sessionmaker[AsyncSession], None]:
    yield async_sessionmaker(async_engine, expire_on_commit=False)


@pytest_asyncio.fixture
async def db_session(
    session_factory: async_sessionmaker[AsyncSession],
) -> AsyncGenerator[AsyncSession, None]:
    async with session_factory() as session:
        yield session


@pytest_asyncio.fixture
async def api_client(
    session_factory: async_sessionmaker[AsyncSession],
) -> AsyncGenerator[AsyncClient, None]:
    async def override_get_db_session() -> AsyncGenerator[AsyncSession, None]:
        async with session_factory() as session:
            try:
                yield session
                await session.commit()
            except Exception:
                await session.rollback()
                raise

    # Clear cache before each test
    cache = RedisCache.get_instance()
    try:
        await cache.delete("analytics:deals:summary:1")
        await cache.delete("analytics:deals:funnel:1")
    except Exception:
        pass  # Ignore cache errors in tests

    app.dependency_overrides[get_db_session] = override_get_db_session
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://testserver") as client:
        yield client
    app.dependency_overrides.pop(get_db_session, None)
