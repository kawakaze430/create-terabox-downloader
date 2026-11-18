"""Source-independent, bounded transfers; no public arbitrary-URL proxy.

Production uses the existing exact-host, DNS-pinned TLS transport. Only explicit
dependency injection replaces that transport for controlled HTTP fixture tests.
Resume is limited to retries within this call, with a strong ETag and known size.
"""
import asyncio
from dataclasses import dataclass, field
from email.utils import parsedate_to_datetime
import hashlib
import hmac
import math
import os
from pathlib import Path
import random
import re
import tempfile
import time
from typing import Callable

import httpx

from .egress import PinnedTransport, UnsafeDestination, approved_url, validate_hosts


class DownloadError(Exception):
    """Bounded codes only: never include an upstream URL, body or exception."""

    def __init__(self, code: str, *, transferred_bytes: int = 0):
        self.code = code
        self.transferred_bytes = transferred_bytes
        super().__init__(code)


@dataclass(frozen=True)
class DownloadSource:
    url: str = field(repr=False)
    allowed_hosts: frozenset[str]
    expected_sha256: str | None = None
    expected_bytes: int | None = None

    def __post_init__(self):
        hosts = validate_hosts(self.allowed_hosts)
        approved_url(self.url, hosts)
        object.__setattr__(self, "allowed_hosts", hosts)
        if self.expected_sha256 is not None and (not isinstance(self.expected_sha256, str) or
                                                not re.fullmatch(r"[0-9a-f]{64}", self.expected_sha256)):
            raise ValueError("Expected SHA-256 must be a lowercase hexadecimal digest.")
        if self.expected_bytes is not None and (type(self.expected_bytes) is not int or not 0 <= self.expected_bytes <= 2**63 - 1):
            raise ValueError("Expected size must be a nonnegative bounded integer.")


@dataclass(frozen=True)
class TransferPolicy:
    max_bytes: int = 1024 * 1024 * 1024
    max_attempts: int = 3
    chunk_bytes: int = 64 * 1024
    connect_timeout: float = 5
    read_timeout: float = 15
    total_timeout: float = 300
    backoff_base: float = 0.25
    backoff_max: float = 5
    max_retry_after: float = 30
    resume: bool = True
    max_transfer_bytes: int | None = None

    def __post_init__(self):
        for name, maximum in (("max_bytes", 2**63 - 1), ("max_attempts", 8), ("chunk_bytes", 1024 * 1024)):
            value = getattr(self, name)
            if type(value) is not int or not 1 <= value <= maximum:
                raise ValueError(f"Invalid {name}.")
        if self.max_transfer_bytes is not None and (
            type(self.max_transfer_bytes) is not int or not 1 <= self.max_transfer_bytes <= 2**63 - 1
        ):
            raise ValueError("Invalid max_transfer_bytes.")
        for name in ("connect_timeout", "read_timeout", "total_timeout", "backoff_base", "backoff_max", "max_retry_after"):
            value = getattr(self, name)
            minimum = 0 if name.startswith("backoff") or name == "max_retry_after" else 0.000001
            if type(value) not in (float, int) or not math.isfinite(value) or not minimum <= value <= 86400:
                raise ValueError(f"Invalid {name}.")
        if self.backoff_base > self.backoff_max or type(self.resume) is not bool:
            raise ValueError("Invalid retry policy.")


@dataclass(frozen=True)
class TransferProgress:
    bytes_written: int
    total_bytes: int | None
    attempt: int
    transferred_bytes: int = 0


@dataclass(frozen=True)
class TransferResult:
    bytes_written: int
    sha256: str
    attempts: int
    resumed: bool
    elapsed_seconds: float
    integrity_verified: bool
    transferred_bytes: int


class _Retry(Exception):
    def __init__(self, delay: float = 0):
        self.delay = delay


def _length(value: str | None) -> int | None:
    if value is None:
        return None
    if not re.fullmatch(r"[0-9]{1,20}", value) or int(value) > 2**63 - 1:
        raise DownloadError("invalid_response")
    return int(value)


def _strong_etag(value: str | None) -> str | None:
    return value if value is not None and re.fullmatch(r'"[\x21\x23-\x7e]{0,256}"', value) else None


def _retry_after(value: str | None, maximum: float) -> float:
    if value is None:
        return 0
    try:
        if re.fullmatch(r"[0-9]+", value):
            # Bound parsing even when a hostile server sends huge digit strings.
            if len(value) > 10:
                raise DownloadError("retry_after_limit")
            delay = float(value)
        else:
            parsed = parsedate_to_datetime(value)
            if parsed.tzinfo is None:
                return 0
            delay = max(0, parsed.timestamp() - time.time())
    except (ValueError, TypeError, OverflowError):
        return 0
    if delay > maximum:
        # Do not cap the value and retry earlier than the source requested.
        raise DownloadError("retry_after_limit")
    return delay


class DownloadEngine:
    def __init__(self, policy: TransferPolicy | None = None, *, transport: httpx.AsyncBaseTransport | None = None):
        self.policy = policy or TransferPolicy()
        self.transport = transport

    async def download(self, source: DownloadSource, destination: Path, *,
                       on_progress: Callable[[TransferProgress], None] | None = None) -> TransferResult:
        """Download into a private same-directory temp file, then publish once.

        No existing destination is replaced, even if created during the transfer.
        Caller supplies a trusted output path; this is not a visitor path API.
        File writes are fixed-size synchronous operations; asyncio deadlines and
        cancellation are cooperative and do not preempt blocked filesystem I/O.
        The optional aggregate budget counts response body bytes received from
        HTTPX. Transport read-ahead can deliver one chunk beyond the limit.
        """
        policy, destination = self.policy, Path(destination)
        if source.expected_bytes is not None and source.expected_bytes > policy.max_bytes:
            raise DownloadError("size_limit")
        if os.path.lexists(destination):
            raise DownloadError("destination_exists")
        started = time.monotonic()
        temporary = None
        transferred = 0
        budget = policy.max_transfer_bytes
        try:
            descriptor, temporary = tempfile.mkstemp(prefix=".download-", suffix=".part", dir=destination.parent)
            with os.fdopen(descriptor, "w+b") as output:
                async with asyncio.timeout(policy.total_timeout):
                    timeout = httpx.Timeout(policy.read_timeout, connect=policy.connect_timeout)
                    async with httpx.AsyncClient(
                        transport=self.transport or PinnedTransport(source.allowed_hosts),
                        trust_env=False, follow_redirects=False, timeout=timeout,
                    ) as client:
                        digest, size, total, etag, resumed = hashlib.sha256(), 0, None, None, False
                        for attempt in range(1, policy.max_attempts + 1):
                            offset = size if policy.resume and etag and total is not None and 0 < size < total else 0
                            if (budget is not None and source.expected_bytes is not None and
                                    transferred + source.expected_bytes - offset > budget):
                                raise DownloadError("transfer_limit")
                            headers = {"Accept-Encoding": "identity"}
                            if offset:
                                headers.update({"Range": f"bytes={offset}-", "If-Range": etag})
                            delay = 0
                            try:
                                async with client.stream("GET", source.url, headers=headers) as response:
                                    status = response.status_code
                                    if status in (429, 500, 502, 503, 504):
                                        raise _Retry(_retry_after(response.headers.get("retry-after"), policy.max_retry_after))
                                    if status not in (200, 206):
                                        raise DownloadError("upstream_status")
                                    if response.headers.get("content-encoding", "identity").lower() != "identity":
                                        raise DownloadError("invalid_response")
                                    length = _length(response.headers.get("content-length"))
                                    if status == 206:
                                        match = re.fullmatch(r"bytes ([0-9]{1,20})-([0-9]{1,20})/([0-9]{1,20})",
                                                             response.headers.get("content-range", ""))
                                        if not offset or not match:
                                            raise DownloadError("invalid_range")
                                        first, last, advertised = map(int, match.groups())
                                        if (first != offset or last != total - 1 or advertised != total or
                                                _strong_etag(response.headers.get("etag")) != etag or
                                                (length is not None and length != total - offset)):
                                            raise DownloadError("invalid_range")
                                        resumed = True
                                    else:
                                        # Range ignored or no safe validator: restart, never append a 200.
                                        if "content-range" in response.headers:
                                            raise DownloadError("invalid_response")
                                        output.seek(0)
                                        output.truncate()
                                        digest, size, resumed = hashlib.sha256(), 0, False
                                        total = length if length is not None else source.expected_bytes
                                        etag = _strong_etag(response.headers.get("etag"))
                                    if total is not None and total > policy.max_bytes:
                                        raise DownloadError("size_limit")
                                    if source.expected_bytes is not None and total != source.expected_bytes:
                                        raise DownloadError("integrity_mismatch")
                                    if budget is not None and total is not None and transferred + total - size > budget:
                                        raise DownloadError("transfer_limit")
                                    received = 0
                                    # Meter raw chunks before splitting into bounded writes so a
                                    # protocol error cannot hide an incomplete buffered chunk.
                                    async for raw in response.aiter_raw():
                                        transferred += len(raw)
                                        if budget is not None and transferred > budget:
                                            raise DownloadError("transfer_limit")
                                        if size + len(raw) > policy.max_bytes:
                                            raise DownloadError("size_limit")
                                        if total is not None and size + len(raw) > total:
                                            raise DownloadError("integrity_mismatch")
                                        data = memoryview(raw)
                                        for start in range(0, len(data), policy.chunk_bytes):
                                            chunk = data[start:start + policy.chunk_bytes]
                                            written = output.write(chunk)
                                            if written != len(chunk):
                                                raise DownloadError("storage_failure")
                                            digest.update(chunk)
                                            size += written
                                            received += written
                                            if on_progress is not None:
                                                on_progress(TransferProgress(size, total, attempt, transferred))
                                            # Observe cancellation even for an already-buffered final chunk.
                                            await asyncio.sleep(0)
                                    if (length is not None and received != length) or (total is not None and size != total):
                                        raise _Retry()
                                break
                            except _Retry as retry:
                                delay = retry.delay
                            except httpx.RequestError:
                                pass  # Retry idempotent GET; no upstream exception/URL escapes.
                            if attempt == policy.max_attempts:
                                raise DownloadError("retry_exhausted")
                            jitter = random.uniform(0, min(policy.backoff_max, policy.backoff_base * 2**(attempt - 1)))
                            await asyncio.sleep(max(delay, jitter))
                        actual_digest = digest.hexdigest()
                        if source.expected_sha256 is not None and not hmac.compare_digest(actual_digest, source.expected_sha256):
                            raise DownloadError("integrity_mismatch")
                        if source.expected_bytes is not None and size != source.expected_bytes:
                            raise DownloadError("integrity_mismatch")
                        output.flush()
                        os.fsync(output.fileno())
                        await asyncio.sleep(0)
                # Same-directory hard link publishes atomically with no overwrite.
                # Unsupported filesystems fail closed; never use a clobber fallback.
                os.link(temporary, destination)
                return TransferResult(size, actual_digest, attempt, resumed, time.monotonic() - started,
                                      source.expected_sha256 is not None, transferred)
        except DownloadError as failure:
            failure.transferred_bytes = transferred
            raise
        except TimeoutError:
            raise DownloadError("timeout", transferred_bytes=transferred) from None
        except UnsafeDestination:
            raise DownloadError("unsafe_destination", transferred_bytes=transferred) from None
        except FileExistsError:
            raise DownloadError("destination_exists", transferred_bytes=transferred) from None
        except OSError:
            raise DownloadError("storage_failure", transferred_bytes=transferred) from None
        finally:
            if temporary is not None:
                Path(temporary).unlink(missing_ok=True)
