from __future__ import annotations

from typing import TypeVar, cast

import redis.asyncio as redis

from mini_crm.config.settings import get_settings

T = TypeVar("T")


class RedisCache:
    """Redis cache client for analytics caching."""

    _instance: RedisCache | None = None
    _redis: redis.Redis | None = None

    def __init__(self) -> None:
        if RedisCache._instance is not None:
            raise RuntimeError("RedisCache is a singleton. Use get_instance() instead.")
        self._initialized = False

    @classmethod
    def get_instance(cls) -> RedisCache:
        """Get singleton instance of RedisCache."""
        if cls._instance is None:
            cls._instance = cls()
        return cls._instance

    async def _ensure_initialized(self) -> None:
        """Initialize Redis connection if not already initialized."""
        if not self._initialized:
            settings = get_settings()
            self._redis = redis.from_url(
                settings.redis_url,
                encoding="utf-8",
                decode_responses=False,
            )
            self._initialized = True

    async def get(self, key: str) -> bytes | None:
        """Get value from cache by key."""
        await self._ensure_initialized()
        if self._redis is None:
            return None
        result = await self._redis.get(key)
        return cast(bytes | None, result)

    async def set(self, key: str, value: bytes, ttl_seconds: int) -> None:
        """Set value in cache with TTL."""
        await self._ensure_initialized()
        if self._redis is None:
            return
        await self._redis.setex(key, ttl_seconds, value)

    async def delete(self, key: str) -> None:
        """Delete key from cache."""
        await self._ensure_initialized()
        if self._redis is None:
            return
        await self._redis.delete(key)

    async def close(self) -> None:
        """Close Redis connection."""
        if self._redis is not None:
            await self._redis.aclose()
            self._redis = None
            self._initialized = False


def serialize_pydantic_model(model: T) -> bytes:
    """Serialize Pydantic model to JSON bytes."""
    if hasattr(model, "model_dump_json"):
        json_str = cast(str, model.model_dump_json())
        return json_str.encode("utf-8")
    raise ValueError("Object is not a Pydantic model")


def deserialize_pydantic_model(data: bytes, model_class: type[T]) -> T:
    """Deserialize JSON bytes to Pydantic model."""
    json_str = data.decode("utf-8")
    if hasattr(model_class, "model_validate_json"):
        validate_method = model_class.model_validate_json  # type: ignore[attr-defined]
        return cast(T, validate_method(json_str))
    raise ValueError("Model class does not support model_validate_json")
