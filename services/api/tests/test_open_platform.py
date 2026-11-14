"""Offline tests for TeraBox's documented, credential-gated OAuth integration."""
import asyncio
import hashlib
from urllib.parse import parse_qs

import httpx
import pytest
from pydantic import SecretStr
from app.open_platform import (
    IntegrationNotReady, OpenPlatformFailure, OpenPlatformOAuth, PartnerCredentials,
    approved_api_origin, authorization_url, oauth_signature,
)

CREDS = PartnerCredentials("sample-client", "secret", "private")


def test_credentials_not_in_repr():
    assert "secret" not in repr(CREDS)
    assert "private" not in repr(CREDS)


def test_missing_environment_configuration_is_safe(monkeypatch):
    for name in ("TERABOX_CLIENT_ID", "TERABOX_CLIENT_SECRET", "TERABOX_PRIVATE_SECRET"):
        monkeypatch.delenv(name, raising=False)
    with pytest.raises(IntegrationNotReady):
        PartnerCredentials.from_environment()


def test_official_authorization_url():
    assert authorization_url(CREDS.client_id) == (
        "https://www.terabox.com/wap/outside/login?clientId=sample-client"
    )


@pytest.mark.parametrize("bad_id", ["", "x", "abc/def", "bad&client", "a" * 257])
def test_invalid_client_ids(bad_id):
    with pytest.raises(ValueError):
        authorization_url(bad_id)


def test_documented_provider_signature():
    text = "sample-client_1705570481_secret_private"
    assert oauth_signature(CREDS, 1705570481) == hashlib.md5(text.encode()).hexdigest()


def test_invalid_signature_timestamps():
    for value in (True, 0, -1, "12"):
        with pytest.raises(ValueError):
            oauth_signature(CREDS, value)


@pytest.mark.parametrize("domain", [
    "127.0.0.1", "https://127.0.0.1", "localhost", "http://www.terabox.com",
    "https://www.terabox.com.evil.example", "https://evil.example@www.terabox.com",
    "https://www.terabox.com@evil.example", "//evil.example", "https://www.terabox.com:9999",
    "https://www.terabox.com/path", "https://www.terabox.com?x=1", "https://www.terabox.com#fragment",
    "https://[::1]", "https://[::1", "https://www.terabox.com.\n",
    "https://www.terabox.com:abc", "www.terabox.com\n",
])
def test_reject_unapproved_api_domains(domain):
    with pytest.raises(IntegrationNotReady):
        approved_api_origin(domain, frozenset({"www.terabox.com"}))


def test_region_hostname_requires_exact_approval():
    allowlist = frozenset({"www.terabox.com"})
    assert approved_api_origin("www.terabox.com", allowlist) == "https://www.terabox.com"
    assert approved_api_origin("https://www.terabox.com/", allowlist) == "https://www.terabox.com"
    with pytest.raises(IntegrationNotReady):
        approved_api_origin("www.terabox.app", allowlist)


def fake_client(handler):
    return httpx.AsyncClient(transport=httpx.MockTransport(handler), trust_env=False)


def test_authorization_exchange_fixed_url_and_masked_tokens():
    def handler(request):
        assert request.method == "POST"
        assert str(request.url) == "https://www.terabox.com/oauth/gettoken"
        params = parse_qs(request.content.decode())
        assert params["grant_type"] == ["authorization_code"]
        assert params["code"] == ["test-code"]
        assert params["sign"] == [oauth_signature(CREDS, 1705570481)]
        return httpx.Response(200, json={"errno": 0, "data": {
            "access_token": "topsecretaccess", "refresh_token": "topsecretrefresh",
            "expires_in": 172800,
        }})

    async def run():
        async with fake_client(handler) as http:
            tokens = await OpenPlatformOAuth(CREDS, http).exchange_code(
                "test-code", timestamp=1705570481,
            )
            assert tokens.access_token.get_secret_value() == "topsecretaccess"
            assert "topsecretaccess" not in repr(tokens)
            assert "topsecretrefresh" not in repr(tokens)

    asyncio.run(run())


def test_token_info_requires_approved_hosts_without_network():
    called = False

    def handler(request):
        nonlocal called
        called = True
        return httpx.Response(200, json={"errno": 0, "data": {"api_domain": "evil.example"}})

    async def run():
        async with fake_client(handler) as http:
            with pytest.raises(IntegrationNotReady):
                await OpenPlatformOAuth(CREDS, http).token_info(SecretStr("access-token"))

    asyncio.run(run())
    assert not called


def test_token_info_accepts_explicitly_approved_regional_host():
    def handler(request):
        assert str(request.url) == "https://www.terabox.com/oauth/tokeninfo"
        assert b"access_token=mytoken" in request.content
        return httpx.Response(200, json={"errno": 0, "data": {
            "api_domain": "www.terabox.app", "user_id": 12345,
        }})

    async def run():
        async with fake_client(handler) as http:
            info, origin = await OpenPlatformOAuth(
                CREDS, http, approved_hosts=frozenset({"www.terabox.app"}),
            ).token_info(SecretStr("mytoken"))
            assert origin == "https://www.terabox.app"
            assert info.user_id == 12345

    asyncio.run(run())


def test_token_info_rejects_unapproved_provider_host():
    for hostname in ("127.0.0.1", "localhost", "evil.example", "www.terabox.app.evil.example"):
        async def run():
            async with fake_client(lambda request: httpx.Response(
                200, json={"errno": 0, "data": {"api_domain": hostname}},
            )) as http:
                with pytest.raises(IntegrationNotReady):
                    await OpenPlatformOAuth(
                        CREDS, http, approved_hosts=frozenset({"www.terabox.com"}),
                    ).token_info(SecretStr("token"))

        asyncio.run(run())


def test_refresh_uses_correct_fixed_endpoint():
    def handler(request):
        assert str(request.url) == "https://www.terabox.com/oauth/refreshtoken"
        assert b"refresh_token=oldtoken" in request.content
        return httpx.Response(200, json={"errno": 0, "data": {
            "access_token": "newaccess", "refresh_token": "newrefresh",
            "expires_in": 172800,
        }})

    async def run():
        async with fake_client(handler) as http:
            tokens = await OpenPlatformOAuth(CREDS, http).refresh(
                SecretStr("oldtoken"), timestamp=1705570481,
            )
            assert tokens.refresh_token.get_secret_value() == "newrefresh"

    asyncio.run(run())


@pytest.mark.parametrize("response", [
    httpx.Response(302, headers={"Location": "http://127.0.0.1/"}),
    httpx.Response(401, text="sensitive_cookie=never_log"),
    httpx.Response(200, text="not JSON"),
    httpx.Response(200, json={"errno": 123, "show_msg": "private_token"}),
    httpx.Response(200, json={"errno": 0, "data": {"access_token": "missing_refresh"}}),
])
def test_upstream_errors_are_sanitized(response):
    async def run():
        async with fake_client(lambda request: response) as http:
            with pytest.raises(OpenPlatformFailure) as exc:
                await OpenPlatformOAuth(CREDS, http).exchange_code(
                    "test-code", timestamp=1705570481,
                )
            assert "sensitive_cookie" not in str(exc.value)
            assert "private_token" not in str(exc.value)

    asyncio.run(run())


def test_reject_oversized_provider_payload():
    async def run():
        async with fake_client(lambda request: httpx.Response(200, content=b"x" * 65537)) as http:
            with pytest.raises(OpenPlatformFailure):
                await OpenPlatformOAuth(CREDS, http).exchange_code(
                    "test-code", timestamp=1705570481,
                )

    asyncio.run(run())


def test_module_is_opt_in():
    assert authorization_url("abcd").startswith("https://www.terabox.com/")


@pytest.mark.parametrize("data", [
    {"access_token": "", "refresh_token": "valid", "expires_in": 172800},
    {"access_token": "valid", "refresh_token": "bad\nvalue", "expires_in": 172800},
    {"access_token": "valid", "refresh_token": "valid", "expires_in": True},
])
def test_invalid_tokens_fail_closed(data):
    async def run():
        async with fake_client(lambda request: httpx.Response(200, json={"errno": 0, "data": data})) as http:
            with pytest.raises(OpenPlatformFailure):
                await OpenPlatformOAuth(CREDS, http).exchange_code("test-code")
    asyncio.run(run())


def test_stream_limit_stops_reading_and_closes_response():
    class Chunks(httpx.AsyncByteStream):
        chunks_read = 0
        closed = False

        async def __aiter__(self):
            for _ in range(1000):
                self.chunks_read += 1
                yield b"x" * 16384

        async def aclose(self):
            self.closed = True

    stream = Chunks()

    async def run():
        async with fake_client(lambda request: httpx.Response(200, stream=stream)) as http:
            with pytest.raises(OpenPlatformFailure):
                await OpenPlatformOAuth(CREDS, http).exchange_code("test-code")
    asyncio.run(run())
    assert stream.chunks_read == 5
    assert stream.closed


def test_compressed_response_is_rejected_without_reading():
    class Unread(httpx.AsyncByteStream):
        async def __aiter__(self):
            raise AssertionError("Compressed response must not be read")
            yield b""

    async def run():
        async with fake_client(lambda request: httpx.Response(
            200, headers={"Content-Encoding": "gzip"}, stream=Unread(),
        )) as http:
            with pytest.raises(OpenPlatformFailure):
                await OpenPlatformOAuth(CREDS, http).exchange_code("test-code")
    asyncio.run(run())
