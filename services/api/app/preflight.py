"""Read-only operator fixture probe. Run without flags for a no-network check."""
import argparse
import asyncio
import json
import logging
import os
import re

import httpx
from pydantic import SecretStr

from .egress import PinnedTransport, validate_hosts
from .links import parse_share_link
from .official_shares import OfficialShares, shorturl, uint, verify_download
from .open_platform import OpenPlatformOAuth, PartnerCredentials

REQUIRED = (
    "TERABOX_CLIENT_ID", "TERABOX_CLIENT_SECRET", "TERABOX_PRIVATE_SECRET",
    "TERABOX_ACCESS_TOKEN", "TERABOX_APPROVED_API_HOSTS", "TERABOX_APPROVED_DOWNLOAD_HOSTS",
    "TERABOX_TEST_SHARE_URL", "TERABOX_TEST_FILE_ID", "TERABOX_TEST_SHA256",
)


def configuration(env):
    """Return only variable names/status; never echo environment values."""
    missing = [name for name in REQUIRED if not env.get(name, "").strip()]
    if env.get("TERABOX_PARTNER_APPROVED") != "true":
        missing.append("TERABOX_PARTNER_APPROVED=true")
    invalid = []
    checks = {
        "TERABOX_CLIENT_ID": lambda: PartnerCredentials(env.get("TERABOX_CLIENT_ID", ""), env.get("TERABOX_CLIENT_SECRET", ""), env.get("TERABOX_PRIVATE_SECRET", "")),
        "TERABOX_APPROVED_API_HOSTS": lambda: validate_hosts(env["TERABOX_APPROVED_API_HOSTS"].split(",")),
        "TERABOX_APPROVED_DOWNLOAD_HOSTS": lambda: validate_hosts(env["TERABOX_APPROVED_DOWNLOAD_HOSTS"].split(",")),
        "TERABOX_TEST_SHARE_URL": lambda: shorturl(parse_share_link(env["TERABOX_TEST_SHARE_URL"])),
        "TERABOX_TEST_FILE_ID": lambda: uint(env["TERABOX_TEST_FILE_ID"]),
    }
    for key, check in checks.items():
        if key not in missing:
            try:
                check()
            except Exception:
                invalid.append(key)
    if "TERABOX_TEST_SHA256" not in missing and not re.fullmatch(r"[0-9a-f]{64}", env["TERABOX_TEST_SHA256"]):
        invalid.append("TERABOX_TEST_SHA256")
    try:
        if not 1 <= int(env.get("TERABOX_TEST_MAX_BYTES", "1048576")) <= 10 * 1024 * 1024:
            raise ValueError()
    except ValueError:
        invalid.append("TERABOX_TEST_MAX_BYTES")
    return {"configuration_ready": not missing and not invalid, "missing": missing, "invalid": invalid,
            "live_verified": False, "public_provider_enabled": False}


async def probe(env):
    creds = PartnerCredentials(env["TERABOX_CLIENT_ID"], env["TERABOX_CLIENT_SECRET"], env["TERABOX_PRIVATE_SECRET"])
    api_hosts = validate_hosts(env["TERABOX_APPROVED_API_HOSTS"].split(","))
    download_hosts = validate_hosts(env["TERABOX_APPROVED_DOWNLOAD_HOSTS"].split(","))
    token = SecretStr(env["TERABOX_ACCESS_TOKEN"])
    # Separate clients keep cookies/authorization isolated from the download CDN.
    async with httpx.AsyncClient(transport=PinnedTransport(api_hosts | {"www.terabox.com"}),
                                 trust_env=False, follow_redirects=False, timeout=8) as api:
        _, origin = await OpenPlatformOAuth(creds, api, approved_hosts=api_hosts).token_info(token)
        shares = OfficialShares(api, origin, token, api_hosts, download_hosts)
        resolved = await shares.resolve(parse_share_link(env["TERABOX_TEST_SHARE_URL"]))
        file_id = str(uint(env["TERABOX_TEST_FILE_ID"]))
        link = await shares.download_link(resolved, file_id)
        selected = next(f for f in resolved.metadata.files if f.file_id == file_id)
        limit = int(env.get("TERABOX_TEST_MAX_BYTES", "1048576"))
        if selected.size_bytes is not None and selected.size_bytes > limit:
            raise ValueError("Fixture exceeds the configured limit.")
    async with httpx.AsyncClient(transport=PinnedTransport(download_hosts), trust_env=False,
                                 follow_redirects=False, timeout=8) as download:
        result = await verify_download(download, link, env["TERABOX_TEST_SHA256"], limit, selected.size_bytes)
    return {"live_verified": True, "metadata_files": len(resolved.metadata.files),
            "download": result, "public_provider_enabled": False}


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--live", action="store_true", help="Use operator-authorized credentials and hash-check one small fixture")
    args = parser.parse_args(argv)
    report = configuration(os.environ)
    if not args.live or not report["configuration_ready"]:
        print(json.dumps(report, sort_keys=True))
        return 0 if report["configuration_ready"] else 2
    # Query parameters can contain credentials; never enable network debug logs.
    for name in ("httpx", "httpcore"):
        logger = logging.getLogger(name)
        logger.setLevel(logging.CRITICAL + 1)
        logger.propagate = False
        logger.disabled = True
    try:
        report = asyncio.run(probe(os.environ))
    except Exception:
        print(json.dumps({"live_verified": False, "error": "PROBE_FAILED",
                          "message": "Provider, network, scope or fixture validation failed. No secrets were logged.",
                          "public_provider_enabled": False}))
        return 1
    print(json.dumps(report, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
