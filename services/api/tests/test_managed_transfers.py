import asyncio
import hashlib
import json
import os
from pathlib import Path
from tempfile import TemporaryDirectory
import time

from fastapi.testclient import TestClient
import httpx
import pytest

from app.download_engine import DownloadEngine
from app.main import create_app
from app import managed_transfers


PREFIX = "/api/v1/transfers"
API = "https://api.example"
WEB = "https://downloads.example"
ACCESS_KEY = "fixture-only-operator-access-key-000000"
SOURCE_URL = "https://source.example/file?signature=private-test-signature"
PAYLOAD = bytes(range(256)) * 1024
SHA256 = hashlib.sha256(PAYLOAD).hexdigest()
pytestmark = pytest.mark.skipif(os.name != "posix" or not hasattr(os, "O_NOFOLLOW"),
                                reason="Managed transfer storage requires POSIX support.")


def registry_source():
    return {"source_id": "fixture", "name": "managed-fixture.bin", "url": SOURCE_URL,
            "size_bytes": len(PAYLOAD), "sha256": SHA256}


@pytest.fixture
def private_test_root(tmp_path):
    candidate = tmp_path.resolve()
    try:
        managed_transfers.require_private_directory(candidate)
    except ValueError:
        # Some sandboxed runtimes give /tmp to an unrelated OS account.
        cache = Path(__file__).resolve().parents[3] / ".pytest_cache"
        cache.mkdir(exist_ok=True)
        with TemporaryDirectory(prefix="managed-tests-", dir=cache) as directory:
            yield Path(directory)
    else:
        yield candidate


@pytest.fixture
def config(private_test_root, monkeypatch):
    registry = private_test_root / "registry.json"
    registry.write_text(json.dumps({"allowed_hosts": ["source.example"], "sources": [registry_source()]}))
    registry.chmod(0o600)
    storage = private_test_root / "storage"
    storage.mkdir(mode=0o700)
    monkeypatch.setenv("TRANSFER_REGISTRY_PATH", str(registry))
    monkeypatch.setenv("TRANSFER_STORAGE_DIR", str(storage))
    monkeypatch.setenv("TRANSFER_ACCESS_KEY", ACCESS_KEY)
    monkeypatch.setenv("ALLOWED_ORIGINS", f"{WEB},http://127.0.0.1:3000")
    return registry, storage


class RegisteredStream(httpx.AsyncByteStream):
    async def __aiter__(self):
        for offset in range(0, len(PAYLOAD), 64 * 1024):
            await asyncio.sleep(0.05)
            yield PAYLOAD[offset:offset + 64 * 1024]


class RegisteredTransport(httpx.AsyncBaseTransport):
    async def handle_async_request(self, request):
        assert str(request.url) == SOURCE_URL
        assert request.method == "GET"
        return httpx.Response(200, headers={"Content-Length": str(len(PAYLOAD))}, stream=RegisteredStream())


@pytest.fixture
def client(config, monkeypatch):
    def engine_factory(policy):
        assert policy.max_bytes == len(PAYLOAD)
        assert policy.max_transfer_bytes == len(PAYLOAD) * 2
        return DownloadEngine(policy, transport=RegisteredTransport())

    monkeypatch.setattr(managed_transfers, "DownloadEngine", engine_factory)
    with TestClient(create_app(), base_url=API) as test_client:
        yield test_client


def session(client):
    response = client.post(f"{PREFIX}/session", json={"access_key": ACCESS_KEY})
    assert response.status_code == 200
    assert response.json()["expires_in"] == managed_transfers.SESSION_TTL
    return {"Authorization": "Bearer " + response.json()["token"]}


def start(client, owner):
    response = client.post(f"{PREFIX}/jobs", json={"source_id": "fixture"}, headers=owner)
    assert response.status_code == 201
    job = response.json()
    return f"{PREFIX}/jobs/{job['id']}", job


def poll(client, path, auth, state):
    deadline = time.monotonic() + 3
    while time.monotonic() < deadline:
        result = client.get(path, headers=auth)
        assert result.status_code == 200
        job = result.json()
        if job["state"] == state:
            return job
        time.sleep(0.04)
    pytest.fail(f"Job did not reach {state!r}")


def test_managed_transfers_disabled_by_default(monkeypatch):
    monkeypatch.delenv("TRANSFER_REGISTRY_PATH", raising=False)
    with TestClient(create_app(), base_url=API) as client:
        assert client.get(f"{PREFIX}/sources").status_code == 404


def test_requires_exact_https_browser_origin(client):
    response = client.post(f"{PREFIX}/session", json={"access_key": ACCESS_KEY}, headers={"Origin": WEB})
    assert response.status_code == 200
    assert response.headers["access-control-allow-origin"] == WEB
    response = client.post(f"{PREFIX}/session", json={"access_key": ACCESS_KEY},
                           headers={"Origin": "https://other.example"})
    assert response.status_code == 403
    assert ACCESS_KEY not in response.text


def test_plain_http_allowed_only_for_direct_loopback(config):
    endpoint = f"{PREFIX}/session"
    url = "http://127.0.0.1:8000"
    with TestClient(create_app(), base_url=url, client=("192.0.2.10", 12345)) as client:
        response = client.post(endpoint, json={"access_key": ACCESS_KEY}, headers={"X-Forwarded-Proto": "https"})
        assert response.status_code == 403
    with TestClient(create_app(), base_url=url, client=("127.0.0.1", 12345)) as client:
        assert client.post(endpoint, json={"access_key": ACCESS_KEY}).status_code == 200
        assert client.post(endpoint, json={"access_key": ACCESS_KEY}, headers={"Host": "other.example"}).status_code == 403


def test_session_credentials_and_registry_fields_redacted(client):
    denied = client.post(f"{PREFIX}/session", json={"access_key": "x" * 40})
    assert denied.status_code == 401
    assert "x" * 40 not in denied.text
    invalid = client.post(f"{PREFIX}/session", json={"access_key": ACCESS_KEY, "extra": ACCESS_KEY})
    assert invalid.status_code == 422
    assert ACCESS_KEY not in invalid.text
    unauthorized = client.get(f"{PREFIX}/sources")
    assert unauthorized.status_code == 401
    assert unauthorized.headers["www-authenticate"] == "Bearer"

    owner = session(client)
    sources = client.get(f"{PREFIX}/sources", headers=owner)
    expected = registry_source()
    del expected["url"]
    assert sources.json() == {"sources": [expected]}
    assert "private-test-signature" not in sources.text
    unknown = client.post(f"{PREFIX}/jobs", json={"source_id": "unknown"}, headers=owner)
    assert unknown.status_code == 404
    forged = client.post(f"{PREFIX}/jobs", json={"source_id": "fixture", "url": SOURCE_URL}, headers=owner)
    assert forged.status_code == 422
    assert SOURCE_URL not in forged.text


def test_managed_job_streams_to_owned_delivery(client):
    owner, other_owner = session(client), session(client)
    path, job = start(client, owner)
    assert job["state"] == "queued" and job["total_bytes"] == len(PAYLOAD)
    assert set(job) == {"id", "state", "bytes_written", "total_bytes", "sha256"}
    for suffix in ("", "/file"):
        assert client.get(path + suffix, headers=other_owner).status_code == 404
    assert client.post(path + "/cancel", headers=other_owner, json={}).status_code == 404
    assert client.get(path + "/file", headers=owner).status_code == 409
    complete = poll(client, path, owner, "completed")
    assert complete["bytes_written"] == len(PAYLOAD) and complete["sha256"] == SHA256
    response = client.get(path + "/file", headers={**owner, "Origin": WEB})
    assert response.status_code == 200
    assert response.headers["content-type"] == "application/octet-stream"
    assert response.headers["content-length"] == str(len(PAYLOAD))
    assert response.headers["content-disposition"] == 'attachment; filename="managed-fixture.bin"'
    assert response.headers["cache-control"] == "no-store"
    assert hashlib.sha256(response.content).hexdigest() == SHA256


def test_cancel_logout_and_owner_quota(client, monkeypatch):
    monkeypatch.setattr(managed_transfers, "MAX_SESSION_STARTS", 1)
    owner = session(client)
    path, _ = start(client, owner)
    assert client.post(f"{PREFIX}/jobs", headers=owner, json={"source_id": "fixture"}).status_code == 429
    cancelled = client.post(path + "/cancel", headers=owner, json={})
    assert cancelled.json()["state"] == "cancelled"
    assert client.get(path + "/file", headers=owner).status_code == 409
    assert client.post(f"{PREFIX}/jobs", headers=owner, json={"source_id": "fixture"}).status_code == 429
    assert client.post(f"{PREFIX}/session/logout", headers=owner, json={}).status_code == 204
    assert client.get(path, headers=owner).status_code == 401


def test_session_expiry_cancels_and_cleans_job(client, config, monkeypatch):
    monkeypatch.setattr(managed_transfers, "SESSION_TTL", 0.15)
    monkeypatch.setattr(managed_transfers, "SWEEP_INTERVAL", 0.02)
    owner = session(client)
    path, job = start(client, owner)
    directory = config[1] / "managed-transfers-v1" / f"job-{job['id']}"
    deadline = time.monotonic() + 3
    while directory.exists() and time.monotonic() < deadline:
        time.sleep(0.02)
    assert not directory.exists()
    assert client.get(path, headers=owner).status_code == 401


def test_storage_lease_and_restart_cleanup(config):
    directory = config[1] / "managed-transfers-v1"
    directory.mkdir(mode=0o700)
    stale = directory / ("job-" + "0" * 32)
    stale.mkdir(mode=0o700)
    (stale / ".download-interrupted.part").write_bytes(b"partial")
    unrelated = config[1] / "operator-note"
    unrelated.write_bytes(b"keep")

    with TestClient(create_app(), base_url=API):
        assert not stale.exists()
        assert unrelated.read_bytes() == b"keep"
        with pytest.raises(RuntimeError, match="exclusive lock"):
            with TestClient(create_app(), base_url=API):
                pytest.fail("Storage permitted two workers.")
    with TestClient(create_app(), base_url=API) as restarted:
        assert restarted.get("/healthz").status_code == 200


def test_bad_storage_fails_startup_without_removing_unexpected_entries(config):
    directory = config[1] / "managed-transfers-v1"
    directory.mkdir(mode=0o700)
    unexpected = directory / "operator-note"
    unexpected.write_bytes(b"keep")
    with pytest.raises(ValueError, match="unexpected entry"):
        with TestClient(create_app(), base_url=API):
            pytest.fail("Storage accepted an unexpected entry.")
    assert unexpected.read_bytes() == b"keep"


@pytest.mark.parametrize("changes", [
    {"name": "../path"}, {"name": 'name"; bad'}, {"size_bytes": 17 * 1024 * 1024},
    {"url": "http://source.example/file"}, {"url": "https://wrong.example/file"},
    {"url": "https://127.0.0.1/file"}, {"sha256": "invalid"}, {"destination": "/path"},
])
def test_registry_fails_closed_without_echoing_private_config(config, changes):
    path, _ = config
    path.write_text(json.dumps({"allowed_hosts": ["source.example"], "sources": [registry_source() | changes]}))
    with pytest.raises(ValueError, match="registry is unsafe or invalid") as caught:
        create_app()
    assert SOURCE_URL not in str(caught.value)
    assert caught.value.__cause__ is None


def test_registry_permissions_and_exact_origins(config, monkeypatch):
    path, _ = config
    path.chmod(0o644)
    with pytest.raises(ValueError, match="registry is unsafe or invalid"):
        create_app()
    path.chmod(0o600)
    monkeypatch.setenv("ALLOWED_ORIGINS", "https://downloads.example/path")
    with pytest.raises(ValueError, match="exact HTTPS"):
        create_app()
