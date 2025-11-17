from __future__ import annotations

from datetime import UTC, datetime

import pytest
from httpx import AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession

from mini_crm.modules.auth.models import OrganizationMember, User
from mini_crm.modules.organizations.models import Organization
from mini_crm.modules.organizations.repositories.sqlalchemy import (
    SQLAlchemyOrganizationRepository,
)
from mini_crm.shared.enums import UserRole

HEADERS = {"Authorization": "Bearer test", "X-Organization-Id": "1"}


async def seed_user_and_org(session: AsyncSession) -> tuple[User, Organization]:
    now = datetime.now(tz=UTC)
    organization = Organization(id=1, name="Acme Inc", created_at=now)
    user = User(
        id=1,
        email="owner@example.com",
        hashed_password="hashed",
        name="Owner",
        created_at=now,
    )
    session.add_all([organization, user])
    await session.commit()
    return user, organization


async def seed_organization_member(
    session: AsyncSession, user_id: int, organization_id: int, role: UserRole = UserRole.OWNER
) -> OrganizationMember:
    member = OrganizationMember(
        user_id=user_id,
        organization_id=organization_id,
        role=role,
    )
    session.add(member)
    await session.flush()
    await session.refresh(member)
    return member


@pytest.mark.asyncio
async def test_sqlalchemy_organization_repository_get_membership_existing(
    db_session: AsyncSession,
) -> None:
    user, organization = await seed_user_and_org(db_session)
    await seed_organization_member(db_session, user.id, organization.id, UserRole.OWNER)
    repository = SQLAlchemyOrganizationRepository(session=db_session)

    membership = await repository.get_membership(user.id, organization.id)

    assert membership is not None
    assert membership.user_id == user.id
    assert membership.organization_id == organization.id
    assert membership.role == UserRole.OWNER


@pytest.mark.asyncio
async def test_sqlalchemy_organization_repository_get_membership_nonexistent(
    db_session: AsyncSession,
) -> None:
    user, organization = await seed_user_and_org(db_session)
    repository = SQLAlchemyOrganizationRepository(session=db_session)

    membership = await repository.get_membership(user.id, organization.id)

    assert membership is None


@pytest.mark.asyncio
async def test_sqlalchemy_organization_repository_get_membership_different_org(
    db_session: AsyncSession,
) -> None:
    now = datetime.now(tz=UTC)
    org1 = Organization(id=1, name="Acme Inc", created_at=now)
    org2 = Organization(id=2, name="Globex LLC", created_at=now)
    user = User(
        id=1,
        email="owner@example.com",
        hashed_password="hashed",
        name="Owner",
        created_at=now,
    )
    db_session.add_all([org1, org2, user])
    await db_session.commit()

    await seed_organization_member(db_session, user.id, org1.id, UserRole.OWNER)
    repository = SQLAlchemyOrganizationRepository(session=db_session)

    membership = await repository.get_membership(user.id, org2.id)

    assert membership is None


@pytest.mark.asyncio
async def test_get_request_context_success(
    api_client: AsyncClient, db_session: AsyncSession
) -> None:
    user, organization = await seed_user_and_org(db_session)
    await seed_organization_member(db_session, user.id, organization.id, UserRole.OWNER)

    response = await api_client.get("/api/v1/system/context", headers=HEADERS)
    assert response.status_code == 200
    data = response.json()
    assert data["user_id"] == user.id
    assert data["organization_id"] == organization.id
    assert data["role"] == UserRole.OWNER.value


@pytest.mark.asyncio
async def test_get_request_context_forbidden_wrong_organization(
    api_client: AsyncClient, db_session: AsyncSession
) -> None:
    now = datetime.now(tz=UTC)
    org1 = Organization(id=1, name="Acme Inc", created_at=now)
    org2 = Organization(id=2, name="Globex LLC", created_at=now)
    user = User(
        id=1,
        email="owner@example.com",
        hashed_password="hashed",
        name="Owner",
        created_at=now,
    )
    db_session.add_all([org1, org2, user])
    await db_session.flush()

    await seed_organization_member(db_session, user.id, org1.id, UserRole.OWNER)

    wrong_headers = {"Authorization": "Bearer test", "X-Organization-Id": "2"}
    response = await api_client.get("/api/v1/system/context", headers=wrong_headers)
    assert response.status_code == 403
    assert "not a member of this organization" in response.json()["detail"]


@pytest.mark.asyncio
async def test_get_request_context_uses_real_role(
    api_client: AsyncClient, db_session: AsyncSession
) -> None:
    user, organization = await seed_user_and_org(db_session)
    await seed_organization_member(db_session, user.id, organization.id, UserRole.MANAGER)

    response = await api_client.get("/api/v1/system/context", headers=HEADERS)
    assert response.status_code == 200
    data = response.json()
    assert data["role"] == UserRole.MANAGER.value
