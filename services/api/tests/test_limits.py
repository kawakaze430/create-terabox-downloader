"""Request admission and privacy boundaries; all tests run without network."""
import asyncio
import json

import pytest
from fastapi.testclient import TestClient
from app.limits import Admission, ApiLimits, RequestGuard
from app.main import create_app, get_provider

URL = "https://terabox.com/s/1Abc_123"
PATH = "/api/v1/shares/resolve"


def test_fixed_window_expires_and_memory_is_bounded():
    now = [0]
    gate = Admission(ApiLimits(requests_per_minute=1, max_clients=1), clock=lambda: now[0])
    assert gate.enter("a") is None
    gate.leave()
    assert gate.enter("a") == ("RATE_LIMITED", 429)
    assert gate.enter("b") == ("SERVICE_BUSY", 503)
    assert len(gate.clients) == 1
    now[0] = 60
    assert gate.enter("b") is None
    gate.leave()
    assert list(gate.clients) == ["b"]


def test_rate_limits_ignore_spoofed_headers_and_preserve_health():
    client = TestClient(create_app(ApiLimits(requests_per_minute=1)))
    assert client.post(PATH, json={"url": URL}).status_code == 501
    r = client.post(PATH, json={"url": URL}, headers={"X-Forwarded-For": "1.2.3.4"})
    assert r.status_code == 429
    assert r.headers["retry-after"] == "60"
    assert r.headers["cache-control"] == "no-store"
    assert client.get("/healthz").status_code == 200


@pytest.mark.parametrize("body", [{"url": {"secret": "DO_NOT_ECHO"}}, {"url": URL, "token": "DO_NOT_ECHO"}, ["DO_NOT_ECHO"], {"url": "DO_NOT_ECHO" * 200}])
def test_validation_errors_never_echo_input(body):
    r = TestClient(create_app()).post(PATH, json=body)
    assert r.status_code == 422
    assert r.json()["error"]["code"] == "INVALID_REQUEST"
    assert "DO_NOT_ECHO" not in r.text


def test_invalid_json_does_not_echo_input():
    r = TestClient(create_app()).post(PATH, content='{"secret":"DO_NOT_ECHO",', headers={"Content-Type": "application/json"})
    assert r.status_code == 422
    assert "DO_NOT_ECHO" not in r.text


def test_declared_oversize_and_content_types_rejected():
    client = TestClient(create_app())
    assert client.post(PATH, content="x" * 4097).status_code == 413
    assert client.post(PATH, content="url=" + URL).status_code == 415
    assert client.post(PATH, json={"url": URL}, headers={"Content-Encoding": "gzip"}).status_code == 415
    r = client.post(PATH, content="x" * 4097, headers={"Origin": "http://localhost:3000"})
    assert r.headers["access-control-allow-origin"] == "http://localhost:3000"


def test_chunked_body_cannot_bypass_limit_and_releases_slot():
    called = []
    async def app(scope, receive, send):
        called.append(True)
    guard = RequestGuard(app, ApiLimits(body_bytes=4, max_inflight=1))
    messages = iter([{"type": "http.request", "body": b"123", "more_body": True},
                     {"type": "http.request", "body": b"456", "more_body": False}])
    responses = []
    async def receive():
        return next(messages)
    async def send(message):
        responses.append(message)
    scope = {"type": "http", "path": PATH, "method": "POST", "headers": [(b"content-type", b"application/json")]}
    asyncio.run(guard(scope, receive, send))
    assert responses[0]["status"] == 413
    assert not called
    assert guard.admission.active == 0


def test_slow_body_times_out_and_releases_slot():
    async def app(*args):
        raise AssertionError("Must not reach application")
    async def receive():
        await asyncio.sleep(1)
    responses = []
    async def send(message):
        responses.append(message)
    guard = RequestGuard(app, ApiLimits(body_timeout_seconds=0.01))
    asyncio.run(guard({"type": "http", "path": PATH, "method": "POST", "headers": [(b"content-type", b"application/json")]}, receive, send))
    assert responses[0]["status"] == 408
    assert guard.admission.active == 0


def test_concurrent_requests_rejected_without_queueing():
    gate = Admission(ApiLimits(max_inflight=1))
    assert gate.enter("a") is None
    assert gate.enter("b") == ("SERVICE_BUSY", 503)
    gate.leave()
    assert gate.enter("b") is None
    gate.leave()


@pytest.mark.parametrize("timeout", [False, True])
def test_provider_failure_is_redacted_or_timed_out(timeout):
    class BrokenProvider:
        configured = True
        async def resolve(self, link):
            if timeout:
                await asyncio.sleep(1)
            raise RuntimeError("access_token=DO_NOT_ECHO")
    app = create_app(ApiLimits(provider_timeout_seconds=0.01))
    app.dependency_overrides[get_provider] = BrokenProvider
    r = TestClient(app).post(PATH, json={"url": URL})
    assert r.status_code == (504 if timeout else 503)
    assert "DO_NOT_ECHO" not in r.text


def test_constructed_models_are_revalidated():
    from app.models import ShareResolution
    class BadProvider:
        configured = True
        async def resolve(self, link):
            return ShareResolution.model_construct(files=[{"file_id": "a", "name": "../escape"}])
    app = create_app()
    app.dependency_overrides[get_provider] = BadProvider
    assert TestClient(app).post(PATH, json={"url": URL}).status_code == 502


@pytest.mark.parametrize("settings", [{"max_inflight": 0}, {"max_clients": -1}, {"provider_timeout_seconds": float("inf")}, {"body_timeout_seconds": float("nan")}])
def test_invalid_limits_fail_startup(settings):
    with pytest.raises(ValueError):
        ApiLimits(**settings)
