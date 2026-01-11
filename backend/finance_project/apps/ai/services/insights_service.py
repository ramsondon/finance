from __future__ import annotations
from typing import Protocol, Dict, Any
from django.conf import settings


class InsightsProvider(Protocol):
    name: str

    def generate_insights(self, user_id: int, context: Dict[str, Any]) -> Dict[str, Any]:
        ...


class ProviderRegistry:
    _providers: dict[str, InsightsProvider] = {}

    @classmethod
    def register(cls, provider: InsightsProvider):
        cls._providers[provider.name] = provider

    @classmethod
    def get_active(cls) -> InsightsProvider:
        name = getattr(settings, "ACTIVE_AI_PROVIDER", "mock")
        provider = cls._providers.get(name)
        if not provider:
            provider = cls._providers.get("mock")
        return provider

