"""Explicit integration seam. Do not substitute unofficial proxy endpoints."""
from typing import Protocol
from .links import ShareLink


class ProviderUnavailable(Exception):
    pass


class ShareProvider(Protocol):
    async def resolve(self, link: ShareLink) -> dict: ...


class UnconfiguredProvider:
    async def resolve(self, link: ShareLink) -> dict:
        raise ProviderUnavailable("No permitted and tested TeraBox integration is configured.")
