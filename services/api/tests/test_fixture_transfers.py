import hashlib
from pathlib import Path
import time

from fastapi.testclient import TestClient
import pytest

from app import fixture_transfers
from app.main import create_app


PREFIX = "/api/v1/fixture-transfers"
HEADER = "X-Transfer-Token"
PEER = ("127.0.0.1", 50000)
BASE_URL = "http://127.0.0.1:8000"


@pytest.fixture
def client(tmp_path, monkeypatch):
    monkeypatch.delenv("ALLOWED_ORIGINS", raising=False)
    monkeypatch.setattr(fixture_transfers.tempfile, "tempdir", str(tmp_path))
    with TestClient(create_app(enable_transfer_fixture=True), base_url=BASE_URL, client=PEER) as test_client:
        yield test_client
    assert not list(tmp_path.iterdir())


def start_job(client):
    source = client.get(f"{PREFIX}/source")
    assert source.status_code == 200
    assert set(source.json()) == {"source_id"}
    response = client.post(f"{PREFIX}/jobs", json=source.json())
    assert response.status_code == 201
    job = response.json()
    return f"{PREFIX}/jobs/{job['id']}", {HEADER: job["token"]}, job


def wait_for_state(client, path, headers, state):
    deadline = time.monotonic() + 5
    counts = []
    while time.monotonic() < deadline:
        response = client.get(path, headers=headers)
        assert response.status_code == 200
        job = response.json()
        counts.append(job["bytes_written"])
        if job["state"] == state:
            return job, counts
        time.sleep(0.1)
    pytest.fail(f"Transfer did not reach {state!r}")


def test_fixture_routes_disabled_by_default(monkeypatch):
    monkeypatch.delenv("ENABLE_TRANSFER_FIXTURE", raising=False)
    with TestClient(create_app(), base_url=BASE_URL, client=PEER) as client:
        assert client.get(f"{PREFIX}/source").status_code == 404


@pytest.mark.parametrize(("peer", "headers"), [
    (("192.0.2.10", 50000), {"X-Forwarded-For": "127.0.0.1"}),
    (PEER, {"Host": "untrusted.example"}),
    (PEER, {"Origin": "https://untrusted.example"}),
])
def test_fixture_requires_local_host_peer_and_origin(monkeypatch, peer, headers):
    monkeypatch.setenv("ENABLE_TRANSFER_FIXTURE", "1")
    monkeypatch.setenv("ALLOWED_ORIGINS", "https://untrusted.example,http://localhost:3000")
    with TestClient(create_app(), base_url=BASE_URL, client=peer) as client:
        assert client.get(f"{PREFIX}/source", headers=headers).status_code == 404


def test_fixture_cors_admits_job_header_for_local_web(client):
    response = client.options(f"{PREFIX}/jobs/demo", headers={
        "Origin": "http://127.0.0.1:3000",
        "Access-Control-Request-Method": "GET",
        "Access-Control-Request-Headers": HEADER,
    })
    assert response.status_code == 200
    assert response.headers["access-control-allow-origin"] == "http://127.0.0.1:3000"
    assert HEADER.lower() in response.headers["access-control-allow-headers"].lower()


def test_fixture_rejects_unknown_source_and_extra_inputs(client):
    target = f"{PREFIX}/jobs"
    assert client.post(target, json={"source_id": "unknown"}).status_code == 404
    source_id = client.get(f"{PREFIX}/source").json()["source_id"]
    for name in ("url", "destination"):
        response = client.post(target, json={"source_id": source_id, name: "private-input"})
        assert response.status_code == 422
        assert "private-input" not in response.text


def test_fixture_streams_progress_and_delivers_verified_bytes(client, tmp_path):
    path, headers, created = start_job(client)
    assert created["state"] == "queued"
    assert created["bytes_written"] == 0
    assert created["total_bytes"] == 262144
    assert created["sha256"] is None
    assert headers[HEADER] not in path
    assert client.get(f"{path}/file", headers=headers).status_code == 409

    completed, counts = wait_for_state(client, path, headers, "completed")
    assert any(0 < count < completed["total_bytes"] for count in counts)
    assert counts == sorted(counts)
    assert completed["bytes_written"] == 262144
    assert "token" not in completed

    download = client.get(f"{path}/file", headers=headers)
    assert download.status_code == 200
    assert download.headers["content-type"] == "application/octet-stream"
    assert download.headers["content-disposition"] == 'attachment; filename="transfer-fixture.bin"'
    assert download.headers["cache-control"] == "no-store"
    assert len(download.content) == int(download.headers["content-length"]) == 262144
    assert download.content == bytes(range(256)) * 1024
    assert hashlib.sha256(download.content).hexdigest() == completed["sha256"]

    directories = list(tmp_path.glob("terabox-fixture-*/" + created["id"]))
    assert len(directories) == 1
    assert directories[0].stat().st_mode & 0o777 == 0o700
    assert [file.name for file in directories[0].iterdir()] == ["transfer-fixture.bin"]


def test_job_token_isolation_and_cancel_cleanup(client, tmp_path, monkeypatch):
    monkeypatch.setattr(fixture_transfers, "CHUNK_DELAY", 0.2)
    path, headers, job = start_job(client)
    other_path, other_headers, _ = start_job(client)
    for foreign in ({}, other_headers):
        assert client.get(path, headers=foreign).status_code == 404
        assert client.get(f"{path}/file", headers=foreign).status_code == 404
        assert client.post(f"{path}/cancel", headers=foreign, json={}).status_code == 404

    response = client.post(f"{path}/cancel", headers=headers, json={})
    assert response.status_code == 200
    assert response.json()["state"] == "cancelled"
    assert client.get(f"{path}/file", headers=headers).status_code == 409
    assert client.get(other_path, headers=other_headers).json()["state"] in ("queued", "running")
    directories = list(tmp_path.glob("terabox-fixture-*/" + job["id"]))
    assert len(directories) == 1
    assert not list(directories[0].iterdir())


def test_fixture_bounds_running_and_retained_jobs(client, monkeypatch):
    monkeypatch.setattr(fixture_transfers, "MAX_RUNNING", 1)
    monkeypatch.setattr(fixture_transfers, "MAX_RETAINED", 2)
    monkeypatch.setattr(fixture_transfers, "CHUNK_DELAY", 0.2)
    source = client.get(f"{PREFIX}/source").json()
    first_path, first_owner, _ = start_job(client)
    assert client.post(f"{PREFIX}/jobs", json=source).status_code == 503
    assert client.post(f"{first_path}/cancel", json={}, headers=first_owner).status_code == 200
    second_path, second_owner, _ = start_job(client)
    assert client.post(f"{second_path}/cancel", json={}, headers=second_owner).status_code == 200
    assert client.post(f"{PREFIX}/jobs", json=source).status_code == 503


def test_fixture_sweeper_expires_completed_files(client, tmp_path, monkeypatch):
    monkeypatch.setattr(fixture_transfers, "JOB_TTL", 0.5)
    monkeypatch.setattr(fixture_transfers, "SWEEP_INTERVAL", 0.02)
    monkeypatch.setattr(fixture_transfers, "CHUNK_DELAY", 0.005)
    path, headers, job = start_job(client)
    wait_for_state(client, path, headers, "completed")
    job_dir, = tmp_path.glob("terabox-fixture-*/" + job["id"])
    assert (job_dir / "transfer-fixture.bin").is_file()

    deadline = time.monotonic() + 3
    while job_dir.exists() and time.monotonic() < deadline:
        time.sleep(0.05)
    assert not job_dir.exists()
    assert client.get(path, headers=headers).status_code == 404
    assert client.get(f"{path}/file", headers=headers).status_code == 404


def test_fixture_integrity_failure_prevents_delivery(client, tmp_path, monkeypatch):
    monkeypatch.setattr(fixture_transfers, "FIXTURE_SHA256", "0" * 64)
    monkeypatch.setattr(fixture_transfers, "CHUNK_DELAY", 0)
    path, headers, job = start_job(client)
    failed, _ = wait_for_state(client, path, headers, "failed")
    assert failed["sha256"] is None
    assert client.get(f"{path}/file", headers=headers).status_code == 409
    job_dir, = tmp_path.glob("terabox-fixture-*/" + job["id"])
    assert not list(job_dir.iterdir())


def test_expired_job_fails_closed_during_cleanup_error(client, monkeypatch):
    monkeypatch.setattr(fixture_transfers, "JOB_TTL", 0.5)
    monkeypatch.setattr(fixture_transfers, "CHUNK_DELAY", 0.005)
    path, headers, job = start_job(client)
    wait_for_state(client, path, headers, "completed")

    remove_tree = fixture_transfers.shutil.rmtree

    def deny_job_cleanup(path, *args, **kwargs):
        if Path(path).name == job["id"]:
            raise PermissionError("fixture cleanup test")
        return remove_tree(path, *args, **kwargs)

    with monkeypatch.context() as patch:
        patch.setattr(fixture_transfers.shutil, "rmtree", deny_job_cleanup)
        time.sleep(0.6)
        assert client.get(f"{path}/file", headers=headers).status_code == 404
