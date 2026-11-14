"""Bounded, single-process API admission controls; no persistent client history."""
import asyncio
from collections import OrderedDict
from dataclasses import dataclass
import math
import os
from threading import Lock
import time

from starlette.responses import JSONResponse


@dataclass(frozen=True)
class ApiLimits:
    body_bytes: int = 4096
    requests_per_minute: int = 60
    max_clients: int = 10000
    max_inflight: int = 16
    body_timeout_seconds: float = 5
    provider_timeout_seconds: float = 10

    def __post_init__(self):
        for name in ("body_bytes", "requests_per_minute", "max_clients", "max_inflight"):
            value = getattr(self, name)
            if type(value) is not int or value < 1:
                raise ValueError(f"{name} must be a positive integer")
        for name in ("body_timeout_seconds", "provider_timeout_seconds"):
            value = getattr(self, name)
            if not math.isfinite(value) or value <= 0:
                raise ValueError(f"{name} must be finite and positive")

    @classmethod
    def from_environment(cls):
        return cls(
            body_bytes=int(os.getenv("API_MAX_BODY_BYTES", "4096")),
            requests_per_minute=int(os.getenv("API_REQUESTS_PER_MINUTE", "60")),
            max_clients=int(os.getenv("API_MAX_RATE_CLIENTS", "10000")),
            max_inflight=int(os.getenv("API_MAX_INFLIGHT", "16")),
            body_timeout_seconds=float(os.getenv("API_BODY_TIMEOUT_SECONDS", "5")),
            provider_timeout_seconds=float(os.getenv("API_PROVIDER_TIMEOUT_SECONDS", "10")),
        )


class Admission:
    """Fixed windows keyed by the ASGI peer; never trust raw forwarded headers.

    Client slots expire after 60 seconds. If full, reject new clients instead of
    evicting active limits. A reverse proxy must sanitize and explicitly trust
    forwarded addresses. Multiple workers require limits at the shared edge.
    """
    def __init__(self, limits, clock=time.monotonic):
        self.limits = limits
        self.clock = clock
        self.clients = OrderedDict()
        self.active = 0
        self.lock = Lock()

    def enter(self, peer):
        with self.lock:
            now = self.clock()
            while self.clients and next(iter(self.clients.values()))[0] <= now:
                self.clients.popitem(last=False)
            if peer not in self.clients:
                if len(self.clients) >= self.limits.max_clients:
                    return "SERVICE_BUSY", 503
                self.clients[peer] = (now + 60, 0)
            expires, count = self.clients[peer]
            if count >= self.limits.requests_per_minute:
                return "RATE_LIMITED", 429
            self.clients[peer] = (expires, count + 1)
            if self.active >= self.limits.max_inflight:
                return "SERVICE_BUSY", 503
            self.active += 1
            return None

    def leave(self):
        with self.lock:
            self.active -= 1


class RequestGuard:
    def __init__(self, app, limits):
        self.app = app
        self.limits = limits
        self.admission = Admission(limits)

    async def __call__(self, scope, receive, send):
        if scope["type"] != "http":
            return await self.app(scope, receive, send)

        async def safe_send(message):
            if message["type"] == "http.response.start":
                headers = list(message.get("headers", []))
                headers.extend([(b"cache-control", b"no-store"),
                                (b"referrer-policy", b"no-referrer"),
                                (b"x-content-type-options", b"nosniff")])
                message = {**message, "headers": headers}
            await send(message)

        async def fail(code, status, message, retry=False):
            response = JSONResponse({"error": {"code": code, "message": message}},
                                    status_code=status,
                                    headers={"Retry-After": "60"} if retry else None)
            await response(scope, receive, safe_send)

        if not scope["path"].startswith("/api/") or scope["method"] == "OPTIONS":
            return await self.app(scope, receive, safe_send)
        peer = (scope.get("client") or ("unknown",))[0]
        rejection = self.admission.enter(peer)
        if rejection:
            code, status = rejection
            return await fail(code, status, "Too many requests. Please try again shortly.", True)
        try:
            headers = dict(scope.get("headers", []))
            length = headers.get(b"content-length")
            if length is not None:
                if not length.isdigit():
                    return await fail("INVALID_REQUEST", 400, "Invalid request length.")
                if len(length) > 10 or int(length) > self.limits.body_bytes:
                    return await fail("REQUEST_TOO_LARGE", 413, "Request body is too large.")
            if headers.get(b"content-encoding", b"identity").lower() != b"identity":
                return await fail("INVALID_REQUEST", 415, "Compressed request bodies are unsupported.")
            if scope["method"] == "POST" and headers.get(b"content-type", b"").split(b";", 1)[0].strip().lower() != b"application/json":
                return await fail("INVALID_REQUEST", 415, "Use an application/json request body.")
            body = bytearray()
            try:
                async with asyncio.timeout(self.limits.body_timeout_seconds):
                    while True:
                        message = await receive()
                        if message["type"] == "http.disconnect":
                            return
                        chunk = message.get("body", b"")
                        if len(body) + len(chunk) > self.limits.body_bytes:
                            return await fail("REQUEST_TOO_LARGE", 413, "Request body is too large.")
                        body.extend(chunk)
                        if not message.get("more_body", False):
                            break
            except TimeoutError:
                return await fail("REQUEST_TIMEOUT", 408, "Request body took too long.")
            delivered = False

            async def replay():
                nonlocal delivered
                if not delivered:
                    delivered = True
                    return {"type": "http.request", "body": bytes(body), "more_body": False}
                return await receive()

            await self.app(scope, replay, safe_send)
        finally:
            self.admission.leave()
