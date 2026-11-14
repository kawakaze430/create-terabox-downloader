import asyncio
import hashlib
import json

import httpx
import pytest
from pydantic import SecretStr
from app.links import parse_share_link
from app.official_shares import OfficialShares, verify_download
from app.open_platform import OpenPlatformFailure
from app.preflight import configuration, main
from app.provider import ProviderError

SHARE = parse_share_link("https://terabox.com/s/1fixture")
BODY = b"An operator-owned, non-sensitive fixture.\n"
METADATA = {"errno": 0, "shareid": 42, "uk": "43", "list": [
    {"fs_id": "99", "isdir": "0", "server_filename": "fixture.txt", "size": str(len(BODY))},
]}


def client(http):
    return OfficialShares(http, "www.terabox.com", SecretStr("secret-access"),
                          {"www.terabox.com"}, {"cdn.example"})


def test_official_metadata_download_and_hash_contract_with_mocks():
    def handler(request):
        if request.url.path == "/openapi/api/shorturlinfo":
            assert request.url.params["shorturl"] == "1fixture"
            assert request.url.params["access_tokens"] == "secret-access"
            return httpx.Response(200, json=METADATA)
        if request.url.path == "/openapi/share/download":
            assert request.url.params["access_token"] == "secret-access"
            assert json.loads(request.url.params["fid_list"]) == [99]
            return httpx.Response(200, json={"errno": 0, "list": [{"fs_id": "99", "isdir": "0", "dlink": "https://cdn.example/fixture?signature=private"}]})
        assert "access_token" not in request.url.params
        assert "cookie" not in request.headers
        return httpx.Response(200, content=BODY)
    async def run():
        async with httpx.AsyncClient(transport=httpx.MockTransport(handler)) as http:
            shares = client(http)
            resolved = await shares.resolve(SHARE)
            assert resolved.metadata.files[0].size_bytes == len(BODY)
            assert resolved.metadata.capabilities.download is False
            assert resolved.metadata.files[0].mime_type is None
            link = await shares.download_link(resolved, "99")
            assert "private" not in repr(link)
            result = await verify_download(http, link, hashlib.sha256(BODY).hexdigest(), 1024, len(BODY))
            assert result == {"verified": True, "bytes": len(BODY)}
    asyncio.run(run())


@pytest.mark.parametrize("payload", [
    {**METADATA, "list": [{"fs_id": True, "isdir": 0, "server_filename": "bad"}]},
    {**METADATA, "list": [{"fs_id": 1, "isdir": 0, "server_filename": "../bad"}]},
    {**METADATA, "list": METADATA["list"] * 2},
    {**METADATA, "errno": False},
    {**METADATA, "uk": -1},
])
def test_malformed_metadata_fails_closed(payload):
    async def run():
        async with httpx.AsyncClient(transport=httpx.MockTransport(lambda request: httpx.Response(200, json=payload))) as http:
            with pytest.raises(OpenPlatformFailure):
                await client(http).resolve(SHARE)
    asyncio.run(run())


@pytest.mark.parametrize("dlink", ["http://cdn.example/file", "https://127.0.0.1/file", "https://evil.example/file", "https://cdn.example/file\n"])
def test_download_destinations_must_be_approved(dlink):
    def handler(request):
        return httpx.Response(200, json=METADATA if request.url.path.endswith("shorturlinfo") else {"errno": 0, "list": [{"fs_id": 99, "isdir": 0, "dlink": dlink}]})
    async def run():
        async with httpx.AsyncClient(transport=httpx.MockTransport(handler)) as http:
            shares = client(http)
            resolved = await shares.resolve(SHARE)
            with pytest.raises(OpenPlatformFailure):
                await shares.download_link(resolved, "99")
    asyncio.run(run())


def test_cannot_request_file_absent_from_resolved_share():
    calls = []
    def handler(request):
        calls.append(request.url.path)
        return httpx.Response(200, json=METADATA)
    async def run():
        async with httpx.AsyncClient(transport=httpx.MockTransport(handler)) as http:
            shares = client(http)
            resolved = await shares.resolve(SHARE)
            with pytest.raises(ProviderError):
                await shares.download_link(resolved, "100")
    asyncio.run(run())
    assert len(calls) == 1


@pytest.mark.parametrize("response,digest,limit", [
    (httpx.Response(302, headers={"Location": "http://127.0.0.1/"}), hashlib.sha256(BODY).hexdigest(), 1024),
    (httpx.Response(200, content=BODY), "0" * 64, 1024),
    (httpx.Response(200, content=BODY), hashlib.sha256(BODY).hexdigest(), 3),
])
def test_download_requires_complete_matching_bounded_bytes(response, digest, limit):
    async def run():
        async with httpx.AsyncClient(transport=httpx.MockTransport(lambda request: response)) as http:
            with pytest.raises(OpenPlatformFailure):
                await verify_download(http, SecretStr("https://cdn.example/file"), digest, limit)
    asyncio.run(run())


def test_preflight_has_no_network_without_explicit_live_flag(monkeypatch, capsys):
    monkeypatch.setenv("TERABOX_CLIENT_SECRET", "DO_NOT_PRINT")
    from app import preflight
    monkeypatch.setattr(preflight, "probe", lambda env: pytest.fail("No network permitted"))
    assert main([]) == 2
    output = capsys.readouterr().out
    assert "DO_NOT_PRINT" not in output
    assert json.loads(output)["live_verified"] is False


def test_preflight_requires_approval_and_all_fixture_configuration():
    report = configuration({})
    assert not report["configuration_ready"]
    assert "TERABOX_PARTNER_APPROVED=true" in report["missing"]
    assert "TERABOX_TEST_SHA256" in report["missing"]


def configured_env():
    return {
        "TERABOX_CLIENT_ID": "fixture-client", "TERABOX_CLIENT_SECRET": "private-client",
        "TERABOX_PRIVATE_SECRET": "private-key", "TERABOX_ACCESS_TOKEN": "operator-token",
        "TERABOX_PARTNER_APPROVED": "true", "TERABOX_APPROVED_API_HOSTS": "www.terabox.com",
        "TERABOX_APPROVED_DOWNLOAD_HOSTS": "cdn.example", "TERABOX_TEST_SHARE_URL": SHARE.normalized_url,
        "TERABOX_TEST_FILE_ID": "99", "TERABOX_TEST_SHA256": hashlib.sha256(BODY).hexdigest(),
    }


def test_operator_probe_end_to_end_with_mocked_network_and_cookie_isolation(monkeypatch):
    from app import preflight
    def handler(request):
        if request.url.path == "/oauth/tokeninfo":
            return httpx.Response(200, headers={"Set-Cookie": "private_session=secret; Path=/"}, json={"errno": 0, "data": {"api_domain": "www.terabox.com"}})
        if request.url.path.endswith("shorturlinfo"):
            return httpx.Response(200, json=METADATA)
        if request.url.path.endswith("download"):
            return httpx.Response(200, json={"errno": 0, "list": [{"fs_id": 99, "isdir": 0, "dlink": "https://cdn.example/file"}]})
        assert request.url.host == "cdn.example"
        assert "cookie" not in request.headers
        assert "authorization" not in request.headers
        assert "operator-token" not in str(request.url)
        return httpx.Response(200, content=BODY)
    monkeypatch.setattr(preflight, "PinnedTransport", lambda hosts: httpx.MockTransport(handler))
    env = configured_env()
    assert configuration(env)["configuration_ready"]
    result = asyncio.run(preflight.probe(env))
    assert result["live_verified"]
    assert result["download"]["bytes"] == len(BODY)
    assert not result["public_provider_enabled"]


def test_failed_live_probe_never_prints_raw_exception(monkeypatch, capsys):
    from app import preflight
    for key, value in configured_env().items():
        monkeypatch.setenv(key, value)
    async def fail(env):
        raise RuntimeError("secret-token-NEVER-PRINT")
    monkeypatch.setattr(preflight, "probe", fail)
    assert main(["--live"]) == 1
    assert "secret-token-NEVER-PRINT" not in capsys.readouterr().out
