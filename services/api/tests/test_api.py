import pytest
from fastapi.testclient import TestClient
from app.main import app
from app.links import parse_share_link

client = TestClient(app)


@pytest.mark.parametrize("url", [
    "https://terabox.com/s/1Abc_123",
    "https://www.teraboxapp.com/s/1Abc-123?utm_source=test",
    "https://terasharefile.com/s/1Abc_123",
    "https://1024terabox.com/sharing/link?surl=1Abc_123&campaign=test",
])
def test_valid_share_urls(url):
    response = client.post("/api/v1/shares/validate", json={"url": url})
    assert response.status_code == 200
    assert response.json()["valid"] is True
    assert "utm_" not in response.json()["normalized_url"]
    assert "campaign=" not in response.json()["normalized_url"]


@pytest.mark.parametrize("url", [
    "http://terabox.com/s/1Abc_123", "https://evil.example/s/1Abc_123",
    "https://terabox.com.evil.example/s/1Abc_123", "https://terabox.com@evil.example/s/1Abc_123",
    "https://user:password@terabox.com/s/1Abc_123", "https://terabox.com:8443/s/1Abc_123",
    "https://terabox.com/other", "https://terabox.com/sharing/link?surl=abc!",
    "https://terabox.com/sharing/link?surl=1Abc_123&surl=other",
    "https://terabox.com/s/%2e%2e%2fadmin", "https://terabox.com/s/abcd\nanything",
])
def test_reject_invalid_links(url):
    response = client.post("/api/v1/shares/validate", json={"url": url})
    assert response.status_code == 400
    assert response.json()["error"]["code"] in ("INVALID_LINK", "UNSUPPORTED_HOST")


def test_normalization_strips_fragment_and_other_query_parameters():
    result = parse_share_link("https://www.terabox.com/s/1Abc_123?pwd=secret#fragment")
    assert result.normalized_url == "https://www.terabox.com/s/1Abc_123"


def test_valid_link_never_claims_download_works():
    response = client.post("/api/v1/shares/resolve", json={"url": "https://terabox.com/s/1Abc_123"})
    assert response.status_code == 501
    assert response.json()["error"]["code"] == "PROVIDER_NOT_CONFIGURED"


def test_bad_link_rejected_before_provider():
    response = client.post("/api/v1/shares/resolve", json={"url": "https://example.net/s/1Abc_123"})
    assert response.status_code == 400


def test_health_reports_provider_state():
    assert client.get("/healthz").json() == {"status": "ok", "provider": "not_configured", "service": "terabox-api"}


def test_cors_only_allows_local_development_site():
    response = client.options("/api/v1/shares/validate", headers={"Origin": "https://untrusted.example", "Access-Control-Request-Method": "POST"})
    assert "access-control-allow-origin" not in response.headers
