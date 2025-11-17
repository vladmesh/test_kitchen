from __future__ import annotations

from collections.abc import AsyncGenerator
from datetime import datetime

import pytest_asyncio
from httpx import ASGITransport, AsyncClient
from sqlalchemy import event
from sqlalchemy.ext.asyncio import (
    AsyncEngine,
    AsyncSession,
    async_sessionmaker,
    create_async_engine,
)
from sqlalchemy.pool import StaticPool

from mini_crm.app.main import app
from mini_crm.core.db import Base
from mini_crm.core.dependencies import get_db_session
from mini_crm.modules.activities import models as activities_models  # noqa: F401
from mini_crm.modules.auth import models as auth_models  # noqa: F401
from mini_crm.modules.contacts import models as contacts_models  # noqa: F401
from mini_crm.modules.deals import models as deals_models  # noqa: F401
from mini_crm.modules.organizations import models as organizations_models  # noqa: F401
from mini_crm.modules.tags import models as tags_models  # noqa: F401
from mini_crm.modules.tasks import models as tasks_models  # noqa: F401


@pytest_asyncio.fixture
async def async_engine() -> AsyncGenerator[AsyncEngine, None]:
    engine = create_async_engine(
        "sqlite+aiosqlite:///:memory:",
        future=True,
        poolclass=StaticPool,
        connect_args={"check_same_thread": False},
    )

    @event.listens_for(engine.sync_engine, "connect")
    def _register_sqlite_functions(dbapi_connection, connection_record) -> None:  # noqa: ANN001
        dbapi_connection.create_function("now", 0, lambda: datetime.utcnow().isoformat())

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

    app.dependency_overrides[get_db_session] = override_get_db_session
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://testserver") as client:
        yield client
    app.dependency_overrides.pop(get_db_session, None)
