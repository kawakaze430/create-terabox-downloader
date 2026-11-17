"""CLI configuration/output contract plus an actual controlled socket transfer."""
import json

from app import download_cli
from app.download_engine import DownloadEngine
from test_download_engine import DIGEST, FIXTURE_URL, PAYLOAD, http_fixture  # noqa: F401


def test_missing_source_returns_safe_configuration_error(monkeypatch, capsys, tmp_path):
    monkeypatch.delenv("ENGINE_SOURCE_URL", raising=False)
    assert download_cli.main([str(tmp_path / "file"), "--host", "fixture.example"]) == 2
    assert json.loads(capsys.readouterr().out) == {"error": {"code": "invalid_configuration"}}
    assert list(tmp_path.iterdir()) == []


def test_cli_downloads_controlled_bytes_and_reports_real_completion(monkeypatch, capsys, tmp_path, http_fixture):
    monkeypatch.setenv("ENGINE_SOURCE_URL", FIXTURE_URL)
    monkeypatch.setattr(download_cli, "DownloadEngine", lambda policy: DownloadEngine(policy, transport=http_fixture.transport()))
    output = tmp_path / "file"
    assert download_cli.main([str(output), "--host", "fixture.example", "--sha256", DIGEST,
                              "--expected-bytes", str(len(PAYLOAD))]) == 0
    text = capsys.readouterr().out
    report = json.loads(text)
    assert report["completed"] and report["integrity_verified"]
    assert report["bytes_written"] == report["transferred_bytes"] == len(PAYLOAD)
    assert output.read_bytes() == PAYLOAD
    assert "signature=" not in text and "private-fixture-value" not in text


def test_cli_integrity_failure_is_redacted_and_cleans_output(monkeypatch, capsys, tmp_path, http_fixture):
    monkeypatch.setenv("ENGINE_SOURCE_URL", FIXTURE_URL)
    monkeypatch.setattr(download_cli, "DownloadEngine", lambda policy: DownloadEngine(policy, transport=http_fixture.transport()))
    assert download_cli.main([str(tmp_path / "file"), "--host", "fixture.example", "--sha256", "0" * 64]) == 1
    assert json.loads(capsys.readouterr().out) == {"error": {"code": "integrity_mismatch"}}
    assert list(tmp_path.iterdir()) == []


def test_cli_applies_aggregate_transfer_budget(monkeypatch, capsys, tmp_path, http_fixture):
    monkeypatch.setenv("ENGINE_SOURCE_URL", FIXTURE_URL)
    monkeypatch.setattr(download_cli, "DownloadEngine", lambda policy: DownloadEngine(policy, transport=http_fixture.transport()))
    assert download_cli.main([str(tmp_path / "file"), "--host", "fixture.example", "--max-transfer-bytes", "1024"]) == 1
    assert json.loads(capsys.readouterr().out) == {"error": {"code": "transfer_limit"}}
    assert len(http_fixture.requests) == 1
    assert list(tmp_path.iterdir()) == []
