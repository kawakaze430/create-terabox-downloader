#!/usr/bin/env python3
"""Measure local transfer recovery, without contacting an external provider.

Run with the API virtual environment. Results are local observations, not a
parallel-transfer speed comparison, production throughput or TeraBox evidence.
"""
import argparse
import asyncio
import hashlib
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
import json
from pathlib import Path
import re
import socket
import statistics
import sys
import tempfile
import threading
import time
import tracemalloc

import httpx

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "services" / "api"))
from app.download_engine import DownloadEngine, DownloadSource, TransferPolicy


class LocalTransport(httpx.AsyncBaseTransport):
    """Explicit fixture-only HTTPS-to-loopback route; never used in production."""

    def __init__(self, port):
        self.port = port
        self.inner = httpx.AsyncHTTPTransport(trust_env=False, retries=0)

    async def handle_async_request(self, request):
        assert request.url.scheme == "https" and request.url.host == "fixture.example"
        local = httpx.Request(request.method,
            request.url.copy_with(scheme="http", host="127.0.0.1", port=self.port),
            headers=request.headers, stream=request.stream, extensions=request.extensions)
        return await self.inner.handle_async_request(local)

    async def aclose(self):
        await self.inner.aclose()


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--size-mib", type=int, choices=range(1, 33), default=4, metavar="1..32")
    parser.add_argument("--repeats", type=int, choices=range(1, 11), default=3, metavar="1..10")
    parser.add_argument("--cut-kib", type=int, choices=(256, 512), default=512)
    args = parser.parse_args()
    payload = bytes(range(256)) * (args.size_mib * 1024 * 1024 // 256)
    expected = hashlib.sha256(payload).hexdigest()
    cut = args.cut_kib * 1024
    etag = '"controlled-fixture-v1"'
    condition = threading.Condition()
    state = {"requests": 0, "completed": 0, "sent": 0, "interrupt": False}

    class Handler(BaseHTTPRequestHandler):
        protocol_version = "HTTP/1.1"

        def log_message(self, *unused):
            pass

        def do_GET(self):
            with condition:
                state["requests"] += 1
                interrupt = state["interrupt"] and state["requests"] == 1
            try:
                offset = 0
                requested = self.headers.get("Range")
                if requested:
                    match = re.fullmatch(r"bytes=([0-9]+)-", requested)
                    if not match or self.headers.get("If-Range") != etag:
                        self.send_error(416)
                        return
                    offset = int(match.group(1))
                    if not 0 < offset < len(payload):
                        self.send_error(416)
                        return
                self.send_response(206 if requested else 200)
                self.send_header("Content-Length", str(len(payload) - offset))
                self.send_header("ETag", etag)
                self.send_header("Connection", "close")
                if requested:
                    self.send_header("Content-Range", f"bytes {offset}-{len(payload)-1}/{len(payload)}")
                self.end_headers()
                end = cut if interrupt else len(payload)
                for start in range(offset, end, 65536):
                    chunk = memoryview(payload)[start:min(start + 65536, end)]
                    self.wfile.write(chunk)
                    with condition:
                        state["sent"] += len(chunk)
                self.wfile.flush()
                if interrupt:
                    self.connection.shutdown(socket.SHUT_RDWR)
            except (BrokenPipeError, ConnectionResetError, OSError):
                pass
            finally:
                self.close_connection = True
                with condition:
                    state["completed"] += 1
                    condition.notify_all()

    server = ThreadingHTTPServer(("127.0.0.1", 0), Handler)
    server.daemon_threads = True
    thread = threading.Thread(target=server.serve_forever, kwargs={"poll_interval": 0.02}, daemon=True)
    thread.start()
    source = DownloadSource("https://fixture.example/owned-test-file", frozenset({"fixture.example"}),
                            expected_sha256=expected, expected_bytes=len(payload))

    def sample(interrupted, resume):
        with condition:
            state.update(requests=0, completed=0, sent=0, interrupt=interrupted)
        settings = TransferPolicy(max_bytes=len(payload), max_attempts=2, resume=resume,
                                  chunk_bytes=65536, backoff_base=0, backoff_max=0)
        with tempfile.TemporaryDirectory(prefix="download-engine-benchmark-") as directory:
            destination = Path(directory) / "verified.bin"

            async def transfer():
                return await DownloadEngine(settings, transport=LocalTransport(server.server_port)).download(source, destination)

            tracemalloc.start()
            started = time.perf_counter()
            try:
                result = asyncio.run(transfer())
                elapsed = time.perf_counter() - started
                peak = tracemalloc.get_traced_memory()[1]
            finally:
                tracemalloc.stop()
            with condition:
                assert condition.wait_for(lambda: state["completed"] == state["requests"], timeout=2)
                sent, requests = state["sent"], state["requests"]
            digest = hashlib.sha256()
            with destination.open("rb") as output:
                while chunk := output.read(65536):
                    digest.update(chunk)
            assert destination.stat().st_size == result.bytes_written == len(payload)
            assert digest.hexdigest() == result.sha256 == expected and result.integrity_verified
            assert result.attempts == requests == (2 if interrupted else 1)
            assert result.resumed is bool(interrupted and resume)
            expected_sent = len(payload) + (cut if interrupted and not resume else 0)
            assert sent == result.transferred_bytes == expected_sent
            return {"elapsed_seconds": elapsed, "server_body_bytes_written": sent,
                    "engine_body_bytes_yielded": result.transferred_bytes, "attempts": result.attempts,
                    "peak_traced_allocations_bytes": peak, "checksum_verified": True}

    try:
        sample(False, False)  # Warm import/client paths before measured samples.
        results = {}
        for label, interrupted, resume in (("clean_stream", False, False),
                                            ("interrupted_restart", True, False),
                                            ("interrupted_resume", True, True)):
            runs = [sample(interrupted, resume) for _ in range(args.repeats)]
            results[label] = {"samples": runs,
                "median_elapsed_seconds": statistics.median(run["elapsed_seconds"] for run in runs),
                "median_peak_traced_allocations_bytes": statistics.median(run["peak_traced_allocations_bytes"] for run in runs)}
        print(json.dumps({"fixture_bytes": len(payload), "interruption_bytes": cut,
            "repeats": args.repeats, "sha256": expected, "scenarios": results,
            "limitations": ["Local HTTP socket fixture through explicit injected transport; no external network or provider.",
                "Sequential transfers only; no parallel-transfer or production speed claim.",
                "Elapsed includes asyncio loop/client setup, transfer, integrity check, filesystem flush and cleanup; tracing is enabled.",
                "Body counters exclude headers/TCP/TLS; server bytes mean successful application writes, not acknowledged wire bytes.",
                "tracemalloc measures process Python allocations including shared server threads; fixture payload preallocation and imports excluded; not RSS.",
                "One clean warmup excluded; OS and filesystem caches are uncontrolled."]}, indent=2))
    finally:
        server.shutdown()
        server.server_close()
        thread.join(timeout=2)
        assert not thread.is_alive()


if __name__ == "__main__":
    main()
