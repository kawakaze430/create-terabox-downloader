"""Start a temporary managed-transfer API for browser acceptance tests."""

from contextlib import nullcontext
import json
import os
from pathlib import Path
import tempfile
from unittest.mock import patch

import httpx
import uvicorn

from app.download_engine import DownloadEngine

HOST = "raw.githubusercontent.com"
URL = (
    "https://raw.githubusercontent.com/sarfiaroui-oss/create-terabox-downloader/"
    "c0163c24ffdcf4391c0e2874cb508f52172958f1/README.md"
)
FIXTURE_BYTES = bytes(range(256)) * 1024
FIXTURE_SHA256 = "2312394bd99545d9de131c24efb781e765ac1aec243f2ed9347597a793a415e9"
LIVE_SIZE = 11078
LIVE_SHA256 = "90ba2d5ad39d0e9a9ff62308ec5588df845550350f87b10ef190593086dfb9dd"


def fixture_engine(*args, **kwargs):
    async def download(request):
        if request.method != "GET" or str(request.url) != URL:
            raise AssertionError("Unexpected transfer target in acceptance test")
        return httpx.Response(200, stream=httpx.ByteStream(FIXTURE_BYTES))

    return DownloadEngine(*args, transport=httpx.MockTransport(download), **kwargs)


def main():
    live = os.environ.get("MANAGED_E2E_LIVE") == "1"
    with tempfile.TemporaryDirectory(prefix="terabox-managed-e2e-") as directory:
        root = Path(directory)
        storage = root / "jobs"
        storage.mkdir(mode=0o700)
        registry = root / "sources.json"
        payload = {
            "allowed_hosts": [HOST],
            "sources": [{
                "source_id": "verified-download",
                "name": "verified-download.bin",
                "url": URL,
                "size_bytes": LIVE_SIZE if live else len(FIXTURE_BYTES),
                "sha256": LIVE_SHA256 if live else FIXTURE_SHA256,
            }],
        }
        descriptor = os.open(registry, os.O_WRONLY | os.O_CREAT | os.O_EXCL, 0o600)
        with os.fdopen(descriptor, "w", encoding="utf-8") as stream:
            json.dump(payload, stream)
        os.environ.update({
            "TRANSFER_REGISTRY_PATH": str(registry),
            "TRANSFER_STORAGE_DIR": str(storage),
            "TRANSFER_ACCESS_KEY": os.environ["MANAGED_E2E_ACCESS_KEY"],
            "ALLOWED_ORIGINS": "http://127.0.0.1:3000",
            "ENABLE_TRANSFER_FIXTURE": "0",
        })
        transport = nullcontext() if live else patch(
            "app.managed_transfers.DownloadEngine", side_effect=fixture_engine,
        )
        with transport:
            from app.main import app

            uvicorn.run(app, host="127.0.0.1", port=8000, proxy_headers=False, access_log=False)


if __name__ == "__main__":
    main()
