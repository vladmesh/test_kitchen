from __future__ import annotations

from datetime import UTC, datetime

import pytest
from httpx import AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession

from mini_crm.core.security import create_access_token
from mini_crm.modules.auth.models import OrganizationMember, User
from mini_crm.modules.organizations.models import Organization
from mini_crm.modules.organizations.repositories.sqlalchemy import (
    SQLAlchemyOrganizationRepository,
)
from mini_crm.shared.enums import UserRole

HEADERS = {
    "Authorization": f"Bearer {create_access_token(1)}",
    "X-Organization-Id": "1",
}


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
    await session.commit()
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

    wrong_headers = {
        "Authorization": f"Bearer {create_access_token(user.id)}",
        "X-Organization-Id": "2",
    }
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


@pytest.mark.asyncio
async def test_list_my_organizations_success(
    api_client: AsyncClient, db_session: AsyncSession
) -> None:
    user, organization = await seed_user_and_org(db_session)
    await seed_organization_member(db_session, user.id, organization.id, UserRole.OWNER)

    headers = {
        "Authorization": f"Bearer {create_access_token(user.id)}",
        "X-Organization-Id": str(organization.id),
    }
    response = await api_client.get("/api/v1/organizations/me", headers=headers)
    assert response.status_code == 200
    data = response.json()
    assert "items" in data
    assert len(data["items"]) == 1
    assert data["items"][0]["id"] == organization.id
    assert data["items"][0]["name"] == organization.name


@pytest.mark.asyncio
async def test_list_my_organizations_multiple_orgs(
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
    await db_session.commit()

    await seed_organization_member(db_session, user.id, org1.id, UserRole.OWNER)
    await seed_organization_member(db_session, user.id, org2.id, UserRole.MEMBER)

    headers = {
        "Authorization": f"Bearer {create_access_token(user.id)}",
        "X-Organization-Id": str(org1.id),
    }
    response = await api_client.get("/api/v1/organizations/me", headers=headers)
    assert response.status_code == 200
    data = response.json()
    assert len(data["items"]) == 2
    org_ids = [item["id"] for item in data["items"]]
    assert org1.id in org_ids
    assert org2.id in org_ids


@pytest.mark.asyncio
async def test_list_my_organizations_excludes_non_member_orgs(
    api_client: AsyncClient, db_session: AsyncSession
) -> None:
    now = datetime.now(tz=UTC)
    org1 = Organization(id=1, name="Acme Inc", created_at=now)
    org2 = Organization(id=2, name="Globex LLC", created_at=now)
    user1 = User(
        id=1,
        email="owner@example.com",
        hashed_password="hashed",
        name="Owner",
        created_at=now,
    )
    user2 = User(
        id=2,
        email="other@example.com",
        hashed_password="hashed",
        name="Other",
        created_at=now,
    )
    db_session.add_all([org1, org2, user1, user2])
    await db_session.commit()

    await seed_organization_member(db_session, user1.id, org1.id, UserRole.OWNER)
    await seed_organization_member(db_session, user2.id, org2.id, UserRole.OWNER)

    headers = {
        "Authorization": f"Bearer {create_access_token(user1.id)}",
        "X-Organization-Id": str(org1.id),
    }
    response = await api_client.get("/api/v1/organizations/me", headers=headers)
    assert response.status_code == 200
    data = response.json()
    assert len(data["items"]) == 1
    assert data["items"][0]["id"] == org1.id
    assert data["items"][0]["name"] == org1.name


@pytest.mark.asyncio
async def test_list_my_organizations_empty_when_no_memberships(
    db_session: AsyncSession,
) -> None:
    now = datetime.now(tz=UTC)
    organization = Organization(id=1, name="Acme Inc", created_at=now)
    user = User(
        id=1,
        email="owner@example.com",
        hashed_password="hashed",
        name="Owner",
        created_at=now,
    )
    db_session.add_all([organization, user])
    await db_session.commit()

    repository = SQLAlchemyOrganizationRepository(session=db_session)
    organizations = await repository.list_for_user(user.id)
    assert len(organizations) == 0


@pytest.mark.asyncio
async def test_sqlalchemy_organization_repository_list_for_user(
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
    await seed_organization_member(db_session, user.id, org2.id, UserRole.MEMBER)

    repository = SQLAlchemyOrganizationRepository(session=db_session)
    organizations = await repository.list_for_user(user.id)

    assert len(organizations) == 2
    org_ids = [org.id for org in organizations]
    assert org1.id in org_ids
    assert org2.id in org_ids
    org_names = {org.id: org.name for org in organizations}
    assert org_names[org1.id] == "Acme Inc"
    assert org_names[org2.id] == "Globex LLC"
