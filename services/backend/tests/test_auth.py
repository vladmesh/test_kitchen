from __future__ import annotations

import pytest
from httpx import AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession


@pytest.mark.asyncio
async def test_register_with_duplicate_organization_name(
    api_client: AsyncClient, db_session: AsyncSession
) -> None:
    """Test that registering with duplicate organization name returns 409 Conflict."""
    # First registration
    first_payload = {
        "email": "user1@example.com",
        "password": "password123",
        "name": "User One",
        "organization_name": "Test Org",
    }
    response = await api_client.post("/api/v1/auth/register", json=first_payload)
    assert response.status_code == 200
    assert "access_token" in response.json()

    # Second registration with same organization name but different email
    second_payload = {
        "email": "user2@example.com",
        "password": "password123",
        "name": "User Two",
        "organization_name": "Test Org",  # Same organization name
    }
    response = await api_client.post("/api/v1/auth/register", json=second_payload)
    assert response.status_code == 409
    assert "Organization with name 'Test Org' already exists" in response.json()["detail"]


@pytest.mark.asyncio
async def test_register_with_unique_organization_name(
    api_client: AsyncClient, db_session: AsyncSession
) -> None:
    """Test that registering with unique organization name succeeds."""
    payload = {
        "email": "unique@example.com",
        "password": "password123",
        "name": "Unique User",
        "organization_name": "Unique Org",
    }
    response = await api_client.post("/api/v1/auth/register", json=payload)
    assert response.status_code == 200
    assert "access_token" in response.json()
    assert "refresh_token" in response.json()
