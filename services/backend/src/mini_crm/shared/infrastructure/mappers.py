from __future__ import annotations

from abc import ABC, abstractmethod
from typing import Generic, TypeVar

TDomain = TypeVar("TDomain")
TInfrastructure = TypeVar("TInfrastructure")


class DomainMapper(ABC, Generic[TDomain, TInfrastructure]):
    """Base mapper for converting between domain and infrastructure models."""

    @abstractmethod
    def to_domain(self, infrastructure_model: TInfrastructure) -> TDomain:
        """Convert infrastructure model to domain entity."""
        raise NotImplementedError

    @abstractmethod
    def to_infrastructure(self, domain_entity: TDomain) -> TInfrastructure:
        """Convert domain entity to infrastructure model."""
        raise NotImplementedError
