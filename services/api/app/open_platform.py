"""Credential-gated client for TeraBox's documented Open Platform OAuth endpoints.

This is NOT yet a downloader or a public login API. An approved partner must
obtain credentials directly from TeraBox. Importing this module makes no calls.
Reference: https://www.terabox.com/integrations/docs?lang=en
"""
from dataclasses import dataclass, field
import asyncio
import hashlib
import ipaddress
import os
import re
import time
from urllib.parse import urlencode, urlsplit

import httpx
from pydantic import BaseModel, ConfigDict, Field, SecretStr, ValidationError, field_validator

OAUTH_ORIGIN = "https://www.terabox.com"
OAUTH_PATHS = frozenset({"/oauth/gettoken", "/oauth/refreshtoken", "/oauth/tokeninfo"})
HOST_PATTERN = re.compile(r"^[a-z0-9-]+(?:\.[a-z0-9-]+)+$")


class IntegrationNotReady(RuntimeError):
    """Partner approval, configuration or regional host review is incomplete."""


class OpenPlatformFailure(RuntimeError):
    """Sanitized failure: never contains upstream bodies or secrets."""


@dataclass(frozen=True)
class PartnerCredentials:
    client_id: str
    client_secret: str = field(repr=False)
    private_secret: str = field(repr=False)

    def __post_init__(self) -> None:
        if not all((self.client_id, self.client_secret, self.private_secret)):
            raise IntegrationNotReady("Approved Open Platform credentials are required.")
        if not re.fullmatch(r"[A-Za-z0-9_-]{4,256}", self.client_id):
            raise IntegrationNotReady("Invalid partner client ID configuration.")

    @classmethod
    def from_environment(cls) -> "PartnerCredentials":
        """Only read server-side secrets; never client-supplied credentials."""
        return cls(
            client_id=os.getenv("TERABOX_CLIENT_ID", ""),
            client_secret=os.getenv("TERABOX_CLIENT_SECRET", ""),
            private_secret=os.getenv("TERABOX_PRIVATE_SECRET", ""),
        )


def authorization_url(client_id: str) -> str:
    """Use TeraBox's own login interface rather than collecting user passwords."""
    if not re.fullmatch(r"[A-Za-z0-9_-]{4,256}", client_id):
        raise ValueError("A valid partner client ID is required.")
    return f"{OAUTH_ORIGIN}/wap/outside/login?{urlencode({'clientId': client_id})}"


def oauth_signature(credentials: PartnerCredentials, timestamp: int) -> str:
    """MD5 signature explicitly specified by TeraBox (not general crypto advice)."""
    if not isinstance(timestamp, int) or isinstance(timestamp, bool) or timestamp <= 0:
        raise ValueError("A positive Unix timestamp is required.")
    text = f"{credentials.client_id}_{timestamp}_{credentials.client_secret}_{credentials.private_secret}"
    return hashlib.md5(text.encode("utf-8")).hexdigest()  # noqa: S324 - required by provider


class OAuthTokens(BaseModel):
    model_config = ConfigDict(extra="ignore", frozen=True)
    access_token: SecretStr
    refresh_token: SecretStr
    expires_in: int = Field(strict=True, gt=0, le=60 * 60 * 24 * 31)

    @field_validator("access_token", "refresh_token")
    @classmethod
    def valid_token(cls, token: SecretStr) -> SecretStr:
        value = token.get_secret_value()
        if not value or len(value) > 8192 or any(ord(c) < 33 or ord(c) == 127 for c in value):
            raise ValueError("Invalid authorization token.")
        return token


class TokenInfo(BaseModel):
    model_config = ConfigDict(extra="ignore", frozen=True)
    api_domain: str = Field(min_length=4, max_length=253)
    upload_domain: str | None = None
    user_id: int | None = None


def approved_api_origin(raw_domain: str, approved_hosts: frozenset[str]) -> str:
    """Require operator-approved EXACT regional hostnames, not suffix matches.

    A region URL supplied in tokeninfo must never become an arbitrary SSRF
    destination. Outbound DNS pinning/network egress policy is still required
    before actually making file API calls to any approved host.
    """
    if (not raw_domain or raw_domain != raw_domain.strip() or
        any(ord(c) < 33 or ord(c) > 126 for c in raw_domain) or
        raw_domain.startswith("//")):
        raise IntegrationNotReady("Unapproved TeraBox API hostname.")
    try:
        parsed = urlsplit(raw_domain if "://" in raw_domain else f"https://{raw_domain}")
        host = (parsed.hostname or "").lower()
        port = parsed.port
    except ValueError:
        raise IntegrationNotReady("Unapproved TeraBox API hostname.") from None
    try:
        ipaddress.ip_address(host)
    except ValueError:
        pass
    else:
        raise IntegrationNotReady("IP addresses are not accepted as API hosts.")
    if (
        parsed.scheme != "https" or parsed.username is not None or parsed.password is not None
        or port not in (None, 443) or parsed.path not in ("", "/") or parsed.query or parsed.fragment
        or not HOST_PATTERN.fullmatch(host) or host not in approved_hosts
    ):
        raise IntegrationNotReady("Unapproved TeraBox API hostname.")
    return f"https://{host}"


class OpenPlatformOAuth:
    """Only requests fixed official OAuth URLs; never arbitrary supplied URLs.

    Caller owns the HTTP client; production callers must use trust_env=False,
    TLS, no redirects, bounded timeouts and network egress controls. An
    injection seam exists for offline MockTransport tests. Never log form data.
    """

    def __init__(self, credentials: PartnerCredentials, http: httpx.AsyncClient,
                 approved_hosts: frozenset[str] = frozenset()):
        self._credentials = credentials
        self._http = http
        self._approved_hosts = approved_hosts

    async def _post_form(self, path: str, form: dict[str, str]) -> dict:
        if path not in OAUTH_PATHS:
            raise IntegrationNotReady("Unrecognized OAuth endpoint.")
        try:
            # Enforce the limit while reading, including for chunked responses.
            # Identity-only avoids allocating an inflated compressed response.
            async with asyncio.timeout(8.0):
                async with self._http.stream(
                    "POST", f"{OAUTH_ORIGIN}{path}", data=form,
                    headers={"Accept-Encoding": "identity"},
                    follow_redirects=False, timeout=8.0,
                ) as response:
                    if response.status_code != 200 or response.headers.get("content-encoding", "identity").lower() != "identity":
                        raise OpenPlatformFailure("TeraBox authorization request failed.")
                    body = bytearray()
                    async for chunk in response.aiter_bytes():
                        if len(body) + len(chunk) > 65536:
                            raise OpenPlatformFailure("TeraBox authorization response is too large.")
                        body.extend(chunk)
        except (httpx.RequestError, TimeoutError):
            raise OpenPlatformFailure("TeraBox authorization service unavailable.") from None
        try:
            import json
            payload = json.loads(body)
        except (ValueError, RecursionError):
            raise OpenPlatformFailure("Invalid TeraBox authorization response.") from None
        if (not isinstance(payload, dict) or type(payload.get("errno")) is not int or payload["errno"] != 0
                or not isinstance(payload.get("data"), dict)):
            raise OpenPlatformFailure("TeraBox authorization was not successful.")
        return payload["data"]

    def _signed(self, timestamp: int) -> dict[str, str]:
        return {
            "client_id": self._credentials.client_id,
            "client_secret": self._credentials.client_secret,
            "timestamp": str(timestamp),
            "sign": oauth_signature(self._credentials, timestamp),
        }

    async def exchange_code(self, code: str, *, timestamp: int | None = None) -> OAuthTokens:
        if not code or len(code) > 1024 or any(ord(c) < 33 for c in code):
            raise ValueError("Invalid authorization code.")
        now = int(time.time()) if timestamp is None else timestamp
        data = await self._post_form("/oauth/gettoken", {
            **self._signed(now), "grant_type": "authorization_code", "code": code,
        })
        try:
            return OAuthTokens.model_validate(data)
        except ValidationError:
            raise OpenPlatformFailure("Incomplete TeraBox authorization response.") from None

    async def refresh(self, refresh_token: SecretStr, *, timestamp: int | None = None) -> OAuthTokens:
        now = int(time.time()) if timestamp is None else timestamp
        data = await self._post_form("/oauth/refreshtoken", {
            **self._signed(now), "refresh_token": refresh_token.get_secret_value(),
        })
        try:
            return OAuthTokens.model_validate(data)
        except ValidationError:
            raise OpenPlatformFailure("Incomplete TeraBox authorization response.") from None

    async def token_info(self, access_token: SecretStr) -> tuple[TokenInfo, str]:
        if not self._approved_hosts:
            raise IntegrationNotReady("Operator-approved TeraBox API hosts are required.")
        data = await self._post_form("/oauth/tokeninfo", {
            "access_token": access_token.get_secret_value(),
        })
        try:
            info = TokenInfo.model_validate(data)
        except ValidationError:
            raise OpenPlatformFailure("Incomplete TeraBox token information.") from None
        return info, approved_api_origin(info.api_domain, self._approved_hosts)
