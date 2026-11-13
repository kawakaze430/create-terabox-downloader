"""Strict, offline-only parsing of known TeraBox share URL shapes.

This module NEVER fetches the supplied URL. Network and redirect safety must
also be enforced by any future provider adapter before it performs HTTP I/O.
"""
from dataclasses import dataclass
import re
from urllib.parse import parse_qs, urlsplit, urlunsplit

ALLOWED_HOSTS = frozenset({
    "terabox.com", "www.terabox.com", "teraboxapp.com", "www.teraboxapp.com",
    "1024terabox.com", "www.1024terabox.com",
    "terasharefile.com", "www.terasharefile.com",
})
TOKEN = re.compile(r"^[A-Za-z0-9_-]{4,128}$")
SHARE_PATH = re.compile(r"^/s/([A-Za-z0-9_-]{4,128})/?$")


class InvalidShareLink(ValueError):
    def __init__(self, code: str, message: str):
        super().__init__(message)
        self.code = code
        self.message = message


@dataclass(frozen=True)
class ShareLink:
    normalized_url: str
    hostname: str
    share_token: str


def parse_share_link(raw: str) -> ShareLink:
    if len(raw) > 2048 or any(ord(char) < 32 or ord(char) == 127 for char in raw):
        raise InvalidShareLink("INVALID_LINK", "Link contains invalid characters or is too long.")
    try:
        value = urlsplit(raw.strip())
        host = (value.hostname or "").lower()
        port = value.port
    except ValueError:
        raise InvalidShareLink("INVALID_LINK", "Malformed URL.") from None
    if value.scheme != "https" or value.username is not None or value.password is not None or port not in (None, 443):
        raise InvalidShareLink("INVALID_LINK", "A standard HTTPS share URL is required.")
    if host not in ALLOWED_HOSTS:
        raise InvalidShareLink("UNSUPPORTED_HOST", "This domain is not on the supported TeraBox allowlist.")

    match = SHARE_PATH.fullmatch(value.path)
    if match:
        token = match.group(1)
        path = f"/s/{token}"
        query = ""
    elif value.path == "/sharing/link":
        params = parse_qs(value.query, keep_blank_values=True)
        tokens = params.get("surl", [])
        if len(tokens) != 1 or not TOKEN.fullmatch(tokens[0]):
            raise InvalidShareLink("INVALID_LINK", "A valid surl share token is required.")
        token = tokens[0]
        path = "/sharing/link"
        query = f"surl={token}"
    else:
        raise InvalidShareLink("INVALID_LINK", "Not a supported share-link path.")
    return ShareLink(urlunsplit(("https", host, path, query, "")), host, token)
