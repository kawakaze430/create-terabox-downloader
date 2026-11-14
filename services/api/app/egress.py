"""Exact-host HTTPS transport with public-address validation and DNS pinning.

For the operator probe, not an arbitrary URL proxy. Connections retain the
original TLS hostname while targeting a validated address. No redirects or
proxy environment variables are followed. Separate pools prevent cross-host
connection reuse when hosts share an IP. httpcore documents sni_hostname at
https://www.encode.io/httpcore/extensions/ .
"""
import asyncio
import ipaddress
import re
import socket
from urllib.parse import urlsplit

import httpx


class UnsafeDestination(ValueError):
    pass


HOST = re.compile(r"[a-z0-9](?:[a-z0-9-]{0,61}[a-z0-9])?(?:\.[a-z0-9](?:[a-z0-9-]{0,61}[a-z0-9])?)+")
TRANSLATION_NETWORKS = tuple(ipaddress.ip_network(n) for n in (
    "64:ff9b::/96", "64:ff9b:1::/48", "2002::/16", "2001::/32",
))


def validate_hosts(hosts):
    result = frozenset(hosts)
    if not result or len(result) > 100:
        raise UnsafeDestination("An exact hostname allowlist is required.")
    for host in result:
        if len(host) > 253 or not HOST.fullmatch(host):
            raise UnsafeDestination("Invalid approved hostname.")
        try:
            ipaddress.ip_address(host)
        except ValueError:
            continue
        raise UnsafeDestination("Literal IP hosts are unsupported.")
    return result


def approved_url(raw, hosts):
    if not isinstance(raw, str) or not raw or len(raw) > 8192 or any(ord(c) < 33 or ord(c) > 126 for c in raw) or "\\" in raw:
        raise UnsafeDestination("Invalid upstream URL.")
    try:
        value = urlsplit(raw)
        valid = (value.scheme == "https" and value.hostname in hosts and
                 value.port in (None, 443) and value.username is None and
                 value.password is None and not value.fragment)
    except ValueError:
        valid = False
    if not valid:
        raise UnsafeDestination("Unapproved upstream URL.")
    return raw


def public_address(value):
    try:
        if "%" in value:
            raise ValueError()
        address = ipaddress.ip_address(value)
    except ValueError:
        raise UnsafeDestination("Invalid upstream address.") from None
    if (not address.is_global or address.is_multicast or address.is_reserved or
        address.is_loopback or address.is_link_local or address.is_unspecified):
        raise UnsafeDestination("Non-public upstream address.")
    if address.version == 6 and (address.ipv4_mapped or any(address in net for net in TRANSLATION_NETWORKS)):
        raise UnsafeDestination("Translated upstream addresses are unsupported.")
    return str(address)


async def resolve_public(host):
    try:
        records = await asyncio.wait_for(
            asyncio.get_running_loop().getaddrinfo(host, 443, type=socket.SOCK_STREAM), 3,
        )
    except (OSError, TimeoutError):
        raise UnsafeDestination("Upstream DNS is unavailable.") from None
    addresses = [public_address(record[4][0]) for record in records]
    if not addresses:
        raise UnsafeDestination("No upstream addresses were returned.")
    # Prefer IPv4 where IPv6 outbound connectivity is unavailable. Every result,
    # including unused results, has already been validated above.
    return sorted(set(addresses), key=lambda addr: ipaddress.ip_address(addr).version)[0]


class PinnedTransport(httpx.AsyncBaseTransport):
    def __init__(self, hosts, *, resolver=resolve_public, transport_factory=None):
        self.hosts = validate_hosts(hosts)
        self.resolver = resolver
        self.factory = transport_factory or (lambda: httpx.AsyncHTTPTransport(
            verify=True, trust_env=False, retries=0,
            limits=httpx.Limits(max_connections=2, max_keepalive_connections=0),
        ))
        self.transports = {}

    async def handle_async_request(self, request):
        approved_url(str(request.url), self.hosts)
        host = request.url.host
        address = public_address(await self.resolver(host))
        transport = self.transports.get(host)
        if transport is None:
            transport = self.transports[host] = self.factory()
        headers = request.headers.copy()
        headers["Host"] = host
        # Do not allow request-level extensions to override destination or tracing.
        extensions = {"timeout": request.extensions.get("timeout", {}), "sni_hostname": host}
        pinned = httpx.Request(request.method, request.url.copy_with(host=address),
                               headers=headers, stream=request.stream, extensions=extensions)
        return await transport.handle_async_request(pinned)

    async def aclose(self):
        for transport in self.transports.values():
            await transport.aclose()
