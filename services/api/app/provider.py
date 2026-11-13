"""Replaceable authorized provider boundary; no live integration yet."""
from enum import StrEnum
from typing import Protocol
from .links import ShareLink
from .models import ShareResolution


class ProviderErrorCode(StrEnum):
    EXPIRED_SHARE = "EXPIRED_SHARE"
    AUTH_REQUIRED = "AUTH_REQUIRED"
    ACCESS_DENIED = "ACCESS_DENIED"
    NOT_FOUND = "NOT_FOUND"
    RATE_LIMITED = "RATE_LIMITED"
    UPSTREAM_UNAVAILABLE = "UPSTREAM_UNAVAILABLE"
    UNSUPPORTED_OPERATION = "UNSUPPORTED_OPERATION"


PUBLIC_ERRORS: dict[ProviderErrorCode, tuple[int, str]] = {
    ProviderErrorCode.EXPIRED_SHARE: (410, "This share link has expired."),
    ProviderErrorCode.AUTH_REQUIRED: (401, "Authorized access is required."),
    ProviderErrorCode.ACCESS_DENIED: (403, "Access is not permitted."),
    ProviderErrorCode.NOT_FOUND: (404, "The shared file was not found."),
    ProviderErrorCode.RATE_LIMITED: (429, "The provider is temporarily limiting requests."),
    ProviderErrorCode.UPSTREAM_UNAVAILABLE: (503, "The provider is temporarily unavailable."),
    ProviderErrorCode.UNSUPPORTED_OPERATION: (501, "The operation is unsupported."),
}


class ProviderError(Exception):
    """Only a bounded code is exposed to users; no upstream text/secrets."""
    def __init__(self, code: ProviderErrorCode):
        self.code = code
        super().__init__(code.value)


class ProviderUnavailable(Exception):
    pass


class ShareProvider(Protocol):
    configured: bool
    async def resolve(self, link: ShareLink) -> ShareResolution: ...


class UnconfiguredProvider:
    configured = False

    async def resolve(self, link: ShareLink) -> ShareResolution:
        raise ProviderUnavailable("No approved and tested integration is configured.")
