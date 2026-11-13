"""Deterministic offline contract tests; no real TeraBox calls."""
from dataclasses import dataclass
import pytest
from fastapi.testclient import TestClient
from app.main import app, get_provider
from app.models import Capabilities, ShareResolution, SharedFile
from app.provider import ProviderError, ProviderErrorCode

URL = "https://terabox.com/s/1Abc_123"
client = TestClient(app)


@dataclass
class FakeProvider:
    result: object
    error: ProviderErrorCode | None = None
    configured: bool = True
    calls: int = 0

    async def resolve(self, link):
        self.calls += 1
        if self.error:
            raise ProviderError(self.error)
        return self.result


@pytest.fixture
def provider():
    fake = FakeProvider(result=ShareResolution(
        files=[SharedFile(file_id="f1", name="test-video.mp4", size_bytes=1024,
                          mime_type="video/mp4", qualities=["source"])],
        capabilities=Capabilities()))
    app.dependency_overrides[get_provider] = lambda: fake
    yield fake
    app.dependency_overrides.pop(get_provider, None)


def test_default_provider_is_not_ready():
    app.dependency_overrides.pop(get_provider, None)
    r = client.get("/readyz")
    assert r.status_code == 503
    assert r.json()["error"]["code"] == "PROVIDER_NOT_CONFIGURED"


def test_offline_provider_contract(provider):
    assert client.get("/readyz").json() == {"ready": True, "provider": "configured"}
    r = client.post("/api/v1/shares/resolve", json={"url": URL})
    assert r.status_code == 200
    data = r.json()
    assert data["files"][0]["name"] == "test-video.mp4"
    assert data["files"][0]["size_bytes"] == 1024
    assert data["capabilities"]["download"] is False
    assert "download_url" not in data["files"][0]
    assert provider.calls == 1


def test_invalid_url_never_calls_provider(provider):
    r = client.post("/api/v1/shares/resolve", json={"url": "https://evil.example/s/abcd"})
    assert r.status_code == 400
    assert provider.calls == 0


@pytest.mark.parametrize("code,status", [
    (ProviderErrorCode.EXPIRED_SHARE, 410),
    (ProviderErrorCode.AUTH_REQUIRED, 401),
    (ProviderErrorCode.ACCESS_DENIED, 403),
    (ProviderErrorCode.NOT_FOUND, 404),
    (ProviderErrorCode.RATE_LIMITED, 429),
    (ProviderErrorCode.UPSTREAM_UNAVAILABLE, 503),
    (ProviderErrorCode.UNSUPPORTED_OPERATION, 501),
])
def test_errors_are_bounded(provider, code, status):
    provider.error = code
    r = client.post("/api/v1/shares/resolve", json={"url": URL})
    assert r.status_code == status
    assert r.json()["error"]["code"] == code.value


@pytest.mark.parametrize("invalid", [
    {"provider": "terabox", "files": [{"file_id": "a", "name": "../escape"}]},
    {"provider": "terabox", "files": [{"file_id": "a", "name": "movie.mp4", "size_bytes": -1}]},
    {"provider": "terabox", "files": [], "cookie": "DO_NOT_LEAK"},
    {"provider": "terabox", "files": [{"file_id": "a", "name": "movie.mp4", "download_url": "https://example.net/secret"}]},
    {"provider": "terabox", "files": [{"file_id": "a", "name": "movie.mp4", "qualities": ["720p", "720p"]}]},
])
def test_invalid_payload_fails_closed_without_leaking(provider, invalid):
    provider.result = invalid
    r = client.post("/api/v1/shares/resolve", json={"url": URL})
    assert r.status_code == 502
    assert r.json()["error"]["code"] == "UPSTREAM_INVALID_RESPONSE"
    assert "DO_NOT_LEAK" not in r.text
    assert "https://example.net/secret" not in r.text


def test_unicode_filenames_are_supported():
    assert SharedFile(file_id="x", name="हिंदी फिल्म.mp4", size_bytes=5).name.endswith(".mp4")


def test_too_many_files_fails_closed(provider):
    provider.result = {"provider": "terabox", "files": [
        {"file_id": str(i), "name": f"{i}.mp4"} for i in range(201)]}
    r = client.post("/api/v1/shares/resolve", json={"url": URL})
    assert r.status_code == 502
