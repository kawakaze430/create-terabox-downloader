import asyncio
import socket

import httpx
import pytest
from app.egress import PinnedTransport, UnsafeDestination, approved_url, public_address, resolve_public, validate_hosts


@pytest.mark.parametrize("address", [
    "127.0.0.1", "10.0.0.1", "169.254.169.254", "192.168.1.2", "100.64.0.1", "0.0.0.0",
    "224.0.0.1", "240.0.0.1", "::1", "fe80::1", "fd00::1", "::ffff:8.8.8.8",
    "64:ff9b::7f00:1", "2002:7f00:1::", "ff02::1", "fe80::1%eth0", "not-an-ip",
])
def test_nonpublic_and_translated_addresses_rejected(address):
    with pytest.raises(UnsafeDestination):
        public_address(address)


@pytest.mark.parametrize("raw", [
    "http://cdn.example/file", "https://cdn.example:444/file", "https://user:secret@cdn.example/file",
    "https://cdn.example.evil/file", "https://cdn.example/file#fragment", "https://cdn.example/file\n",
    "https://cdn.example\\@evil/file", "https://127.0.0.1/file", "//cdn.example/file",
])
def test_unapproved_urls_rejected(raw):
    with pytest.raises(UnsafeDestination):
        approved_url(raw, {"cdn.example"})


def test_pool_connection_targets_pinned_ip_with_original_tls_name():
    looked_up = []
    requests = []
    async def resolver(host):
        looked_up.append(host)
        return "8.8.8.8"
    def handler(request):
        requests.append(request)
        assert request.url.host == "8.8.8.8"
        assert request.headers["host"] == "cdn.example"
        assert request.extensions["sni_hostname"] == "cdn.example"
        assert "trace" not in request.extensions
        return httpx.Response(200, text="fixture")
    async def run():
        transport = PinnedTransport({"cdn.example"}, resolver=resolver,
                                    transport_factory=lambda: httpx.MockTransport(handler))
        async with httpx.AsyncClient(transport=transport) as http:
            response = await http.get("https://cdn.example/fixture")
            assert response.text == "fixture"
            with pytest.raises(UnsafeDestination):
                await http.get("https://evil.example/fixture")
    asyncio.run(run())
    assert looked_up == ["cdn.example"]
    assert len(requests) == 1


def test_dns_with_mixed_public_and_private_answers_fails_closed(monkeypatch):
    async def run():
        loop = asyncio.get_running_loop()
        async def records(*args, **kwargs):
            return [(socket.AF_INET, socket.SOCK_STREAM, 6, "", (ip, 443)) for ip in ["8.8.8.8", "127.0.0.1"]]
        monkeypatch.setattr(loop, "getaddrinfo", records)
        with pytest.raises(UnsafeDestination):
            await resolve_public("cdn.example")
    asyncio.run(run())


def test_dns_rebinding_never_reaches_a_private_destination():
    calls = []
    answers = iter(["8.8.8.8", "127.0.0.1"])
    async def resolver(host):
        return next(answers)
    def handler(request):
        calls.append(str(request.url))
        return httpx.Response(200)
    async def run():
        async with httpx.AsyncClient(transport=PinnedTransport({"cdn.example"}, resolver=resolver,
              transport_factory=lambda: httpx.MockTransport(handler))) as http:
            await http.get("https://cdn.example/a")
            with pytest.raises(UnsafeDestination):
                await http.get("https://cdn.example/b")
    asyncio.run(run())
    assert calls == ["https://8.8.8.8/a"]


@pytest.mark.parametrize("hosts", [set(), {"127.0.0.1"}, {"*.terabox.com"}, {"cdn.example:443"}, {"localhost"}, {"-bad.example"}])
def test_host_configuration_is_exact(hosts):
    with pytest.raises(UnsafeDestination):
        validate_hosts(hosts)
