from __future__ import annotations

from mini_crm.config.settings import get_settings
from mini_crm.core.cache import (
    RedisCache,
    deserialize_pydantic_model,
    serialize_pydantic_model,
)
from mini_crm.modules.analytics.dto.schemas import DealsFunnel, DealsSummary
from mini_crm.modules.analytics.repositories.repository import AbstractAnalyticsRepository
from mini_crm.modules.common.application.context import RequestContext


class GetDealsSummaryUseCase:
    """Use case for getting deals summary."""

    def __init__(
        self,
        repository: AbstractAnalyticsRepository,
        cache: RedisCache,
    ) -> None:
        self.repository = repository
        self.cache = cache

    async def execute(self, context: RequestContext) -> DealsSummary:
        """Get deals summary for the organization."""
        organization_id = context.organization.organization_id
        cache_key = f"analytics:deals:summary:{organization_id}"

        # Try to get from cache
        cached_data = await self.cache.get(cache_key)
        if cached_data is not None:
            return deserialize_pydantic_model(cached_data, DealsSummary)

        # Get from repository
        result = await self.repository.deals_summary(organization_id)

        # Store in cache
        settings = get_settings()
        serialized = serialize_pydantic_model(result)
        await self.cache.set(cache_key, serialized, settings.analytics_cache_ttl_seconds)

        return result


class GetDealsFunnelUseCase:
    """Use case for getting deals funnel."""

    def __init__(
        self,
        repository: AbstractAnalyticsRepository,
        cache: RedisCache,
    ) -> None:
        self.repository = repository
        self.cache = cache

    async def execute(self, context: RequestContext) -> DealsFunnel:
        """Get deals funnel for the organization."""
        organization_id = context.organization.organization_id
        cache_key = f"analytics:deals:funnel:{organization_id}"

        # Try to get from cache
        cached_data = await self.cache.get(cache_key)
        if cached_data is not None:
            return deserialize_pydantic_model(cached_data, DealsFunnel)

        # Get from repository
        result = await self.repository.deals_funnel(organization_id)

        # Store in cache
        settings = get_settings()
        serialized = serialize_pydantic_model(result)
        await self.cache.set(cache_key, serialized, settings.analytics_cache_ttl_seconds)

        return result
