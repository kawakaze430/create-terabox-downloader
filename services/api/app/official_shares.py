"""Operator-only official share API candidate; live compatibility is unverified.

Based on the documented shorturlinfo and share/download contracts. This module
is NOT enabled on public API routes and does not implement account-wide access.
"""
import asyncio
from dataclasses import dataclass, field
import hashlib
import hmac
import json
import re
from urllib.parse import urlsplit

import httpx
from pydantic import SecretStr, ValidationError

from .egress import UnsafeDestination, approved_url, validate_hosts
from .links import ShareLink
from .models import ShareResolution, SharedFile
from .open_platform import OpenPlatformFailure, approved_api_origin
from .provider import ProviderError, ProviderErrorCode


def uint(value):
    if type(value) is int:
        number = value
    elif isinstance(value, str) and re.fullmatch(r"[0-9]{1,20}", value):
        number = int(value)
    else:
        raise OpenPlatformFailure("Invalid upstream integer.")
    if not 0 <= number <= 2**64 - 1:
        raise OpenPlatformFailure("Invalid upstream integer.")
    return number


def shorturl(link: ShareLink):
    # The documentation uses /s/1xxx. Legacy surl semantics need live evidence.
    if not urlsplit(link.normalized_url).path.startswith("/s/1") or len(link.share_token) < 5:
        raise ProviderError(ProviderErrorCode.UNSUPPORTED_OPERATION)
    return link.share_token


@dataclass(frozen=True)
class ResolvedShare:
    metadata: ShareResolution
    share_id: int = field(repr=False)
    owner_id: int = field(repr=False)


async def bounded_json(http, url, *, params):
    try:
        async with asyncio.timeout(10):
            async with http.stream("GET", url, params=params, follow_redirects=False,
                                   headers={"Accept-Encoding": "identity"}, timeout=8) as response:
                if response.status_code == 429:
                    raise ProviderError(ProviderErrorCode.RATE_LIMITED)
                if response.status_code in (401, 403):
                    raise ProviderError(ProviderErrorCode.AUTH_REQUIRED)
                if response.status_code != 200 or response.headers.get("content-encoding", "identity").lower() != "identity":
                    raise OpenPlatformFailure("Share API request failed.")
                body = bytearray()
                async for chunk in response.aiter_bytes():
                    if len(body) + len(chunk) > 1024 * 1024:
                        raise OpenPlatformFailure("Share response exceeds the size limit.")
                    body.extend(chunk)
        payload = json.loads(body)
    except (httpx.RequestError, TimeoutError, ValueError, RecursionError):
        raise OpenPlatformFailure("Share API response is unavailable or invalid.") from None
    if not isinstance(payload, dict) or type(payload.get("errno")) is not int:
        raise OpenPlatformFailure("Invalid share API envelope.")
    code = payload["errno"]
    if code in (-9, -12):
        raise ProviderError(ProviderErrorCode.AUTH_REQUIRED)
    if code == 105:
        raise ProviderError(ProviderErrorCode.NOT_FOUND)
    if code != 0:
        raise OpenPlatformFailure("Share API rejected the request.")
    return payload


class OfficialShares:
    def __init__(self, http, origin, token: SecretStr, approved_api_hosts, download_hosts):
        self.http = http
        self.origin = approved_api_origin(origin, validate_hosts(approved_api_hosts))
        self.token = token
        self.download_hosts = validate_hosts(download_hosts)
        value = token.get_secret_value()
        if not value or len(value) > 8192 or any(ord(c) < 33 or ord(c) == 127 for c in value):
            raise OpenPlatformFailure("A valid operator access token is required.")

    async def resolve(self, link):
        payload = await bounded_json(self.http, self.origin + "/openapi/api/shorturlinfo", params={
            "access_tokens": self.token.get_secret_value(), "shorturl": shorturl(link), "root": "1", "spd": "",
        })
        files = payload.get("list")
        if not isinstance(files, list) or len(files) > 200:
            raise OpenPlatformFailure("Unsupported share listing.")
        try:
            result = []
            ids = set()
            for item in files:
                if not isinstance(item, dict):
                    raise ValueError()
                file_id = str(uint(item.get("fs_id")))
                kind = uint(item.get("isdir"))
                if kind not in (0, 1) or file_id in ids:
                    raise ValueError()
                ids.add(file_id)
                result.append(SharedFile(file_id=file_id, name=item.get("server_filename"),
                    kind="folder" if kind else "file",
                    size_bytes=None if kind or item.get("size") is None else uint(item["size"])))
            return ResolvedShare(ShareResolution(files=result), uint(payload.get("shareid")), uint(payload.get("uk")))
        except (ValidationError, ValueError):
            raise OpenPlatformFailure("Invalid share metadata.") from None

    async def download_link(self, share: ResolvedShare, file_id: str):
        selected = next((f for f in share.metadata.files if f.file_id == file_id and f.kind == "file"), None)
        if selected is None:
            raise ProviderError(ProviderErrorCode.NOT_FOUND)
        # Singular access_token follows the parameter table. Documentation curl
        # samples disagree; do not retry alternative protocols without evidence.
        payload = await bounded_json(self.http, self.origin + "/openapi/share/download", params={
            "access_token": self.token.get_secret_value(), "shareid": str(share.share_id),
            "uk": str(share.owner_id), "fid_list": json.dumps([uint(file_id)]), "sekey": "",
        })
        files = payload.get("list")
        if not isinstance(files, list) or len(files) != 1 or not isinstance(files[0], dict):
            raise OpenPlatformFailure("Unexpected download response.")
        item = files[0]
        # Docs use fid_id in the table and fs_id in their response example.
        candidates = [uint(item[key]) for key in ("fs_id", "fid_id") if key in item]
        if not candidates or any(value != uint(file_id) for value in candidates) or uint(item.get("isdir")) != 0:
            raise OpenPlatformFailure("Download file did not match the selection.")
        try:
            return SecretStr(approved_url(item.get("dlink"), self.download_hosts))
        except UnsafeDestination:
            raise OpenPlatformFailure("Download host has not been approved.") from None


async def verify_download(http, url: SecretStr, expected_sha256, max_bytes, expected_bytes=None):
    """Hash a small authorized test file; never persist or print its URL/content."""
    if not re.fullmatch(r"[0-9a-f]{64}", expected_sha256) or type(max_bytes) is not int or not 1 <= max_bytes <= 10 * 1024 * 1024:
        raise ValueError("Use a SHA-256 digest and a limit of at most 10 MiB.")
    digest, size = hashlib.sha256(), 0
    try:
        async with asyncio.timeout(30):
            async with http.stream("GET", url.get_secret_value(), follow_redirects=False,
                                   headers={"Accept-Encoding": "identity"}, timeout=8) as response:
                if response.status_code != 200 or response.headers.get("content-encoding", "identity").lower() != "identity":
                    raise OpenPlatformFailure("Test download was refused or redirected.")
                async for chunk in response.aiter_bytes():
                    size += len(chunk)
                    if size > max_bytes:
                        raise OpenPlatformFailure("Test download exceeded its byte limit.")
                    digest.update(chunk)
    except (httpx.RequestError, TimeoutError, UnsafeDestination):
        raise OpenPlatformFailure("Test download failed.") from None
    if (expected_bytes is not None and size != expected_bytes) or not hmac.compare_digest(digest.hexdigest(), expected_sha256):
        raise OpenPlatformFailure("Downloaded bytes did not match the expected fixture.")
    return {"verified": True, "bytes": size}
