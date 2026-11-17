"""Source-neutral transfer checks against a real local HTTP socket fixture.

The fixture transport is deliberately injected: production source admission
still requires approved public HTTPS hosts, with no localhost exception.
These tests prove controlled HTTP transfer behavior, not TeraBox access.
"""
import asyncio
from dataclasses import dataclass, field
from datetime import datetime, timedelta, timezone
from email.utils import format_datetime
import hashlib
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
import socket
import threading
import time

import httpx
import pytest

from app.download_engine import DownloadEngine, DownloadError, DownloadSource, TransferPolicy


PAYLOAD = bytes(range(256)) * 1024
DIGEST = hashlib.sha256(PAYLOAD).hexdigest()
FIXTURE_URL = "https://fixture.example/file?signature=private-fixture-value"


@dataclass
class Reply:
    status: int = 200
    body: bytes = PAYLOAD
    headers: dict[str, str] = field(default_factory=dict)
    cut_after: int | None = None
    omit_length: bool = False
    body_delay: float = 0


class FixtureTransport(httpx.AsyncBaseTransport):
    """Route one admitted test host to the explicit local fixture only."""

    def __init__(self, port):
        self.port = port
        self.inner = httpx.AsyncHTTPTransport(trust_env=False, retries=0)

    async def handle_async_request(self, request):
        assert request.url.scheme == "https"
        assert request.url.host == "fixture.example"
        local = httpx.Request(
            request.method,
            request.url.copy_with(scheme="http", host="127.0.0.1", port=self.port),
            headers=request.headers,
            stream=request.stream,
            extensions=request.extensions,
        )
        return await self.inner.handle_async_request(local)

    async def aclose(self):
        await self.inner.aclose()


class HttpFixture:
    def __init__(self):
        self.requests = []
        self.replies = [Reply()]
        self.lock = threading.Lock()

    def reply_for(self, path, headers):
        with self.lock:
            self.requests.append({"path": path, "headers": {key.lower(): value for key, value in headers.items()}})
            index = len(self.requests) - 1
            return self.replies[min(index, len(self.replies) - 1)]

    def transport(self):
        return FixtureTransport(self.server.server_port)


@pytest.fixture
def http_fixture():
    fixture = HttpFixture()

    class Handler(BaseHTTPRequestHandler):
        protocol_version = "HTTP/1.1"

        def log_message(self, *args):
            # Never print private query strings, including on fixture failures.
            pass

        def do_GET(self):
            reply = fixture.reply_for(self.path, self.headers)
            self.send_response(reply.status)
            if not reply.omit_length and "Content-Length" not in reply.headers:
                self.send_header("Content-Length", str(len(reply.body)))
            self.send_header("Connection", "close")
            for name, value in reply.headers.items():
                self.send_header(name, value)
            self.end_headers()
            data = reply.body if reply.cut_after is None else reply.body[:reply.cut_after]
            try:
                if reply.body_delay:
                    time.sleep(reply.body_delay)
                self.wfile.write(data)
                self.wfile.flush()
                if reply.cut_after is not None:
                    self.connection.shutdown(socket.SHUT_RDWR)
            except (BrokenPipeError, ConnectionResetError, OSError):
                pass
            self.close_connection = True

    server = ThreadingHTTPServer(("127.0.0.1", 0), Handler)
    server.daemon_threads = True
    fixture.server = server
    worker = threading.Thread(target=server.serve_forever, kwargs={"poll_interval": 0.02}, daemon=True)
    worker.start()
    try:
        yield fixture
    finally:
        server.shutdown()
        server.server_close()
        worker.join(timeout=2)
        assert not worker.is_alive()


def source(**kwargs):
    return DownloadSource(FIXTURE_URL, frozenset({"fixture.example"}), **kwargs)


def policy(**kwargs):
    values = {"max_bytes": len(PAYLOAD) * 2, "chunk_bytes": 4096,
              "backoff_base": 0.001, "backoff_max": 0.01}
    values.update(kwargs)
    return TransferPolicy(**values)


def run_download(fixture, destination, *, settings=None, selected=None, progress=None):
    async def run():
        return await DownloadEngine(policy=settings or policy(), transport=fixture.transport()).download(
            selected or source(expected_sha256=DIGEST, expected_bytes=len(PAYLOAD)),
            destination, on_progress=progress,
        )
    return asyncio.run(run())


def assert_clean(directory):
    assert list(directory.iterdir()) == [], "Failed transfer left destination or temporary files"


@pytest.mark.parametrize("url,hosts", [
    ("http://fixture.example/file", {"fixture.example"}),
    ("https://127.0.0.1/file", {"127.0.0.1"}),
    ("https://localhost/file", {"localhost"}),
    ("https://fixture.example.evil/file", {"fixture.example"}),
    ("https://user:private@fixture.example/file", {"fixture.example"}),
    ("https://fixture.example:444/file", {"fixture.example"}),
    ("https://fixture.example/file#private", {"fixture.example"}),
    (FIXTURE_URL, set()),
])
def test_sources_do_not_admit_private_http_or_unapproved_destinations(url, hosts):
    with pytest.raises((ValueError, DownloadError)):
        DownloadSource(url, frozenset(hosts))


def test_source_repr_does_not_reveal_private_url():
    assert "private-fixture-value" not in repr(source())
    assert "signature=" not in repr(source())


def test_complete_stream_verifies_bytes_hash_and_atomic_publication(http_fixture, tmp_path):
    destination = tmp_path / "download.bin"
    events = []

    def progress(event):
        assert not destination.exists(), "Partial bytes became visible at final path"
        events.append(event)

    result = run_download(http_fixture, destination, progress=progress)
    assert destination.read_bytes() == PAYLOAD
    assert result.bytes_written == len(PAYLOAD)
    assert result.sha256 == DIGEST
    assert result.integrity_verified is True
    assert result.attempts == 1
    assert result.resumed is False
    assert result.elapsed_seconds >= 0
    assert [event.bytes_written for event in events] == sorted(event.bytes_written for event in events)
    assert events[-1].bytes_written == len(PAYLOAD)
    assert all(event.total_bytes == len(PAYLOAD) and event.attempt == 1 for event in events)
    assert len(events) > 1
    assert list(tmp_path.iterdir()) == [destination]
    assert len(http_fixture.requests) == 1
    assert http_fixture.requests[0]["headers"]["accept-encoding"] == "identity"


def test_unknown_length_stream_is_bounded_and_hashed(http_fixture, tmp_path):
    http_fixture.replies = [Reply(omit_length=True)]
    result = run_download(http_fixture, tmp_path / "output", selected=source())
    assert result.bytes_written == len(PAYLOAD)
    assert result.sha256 == DIGEST
    assert result.integrity_verified is False, "Calculated hash alone is not trusted checksum verification"


def test_empty_file_is_a_valid_completed_transfer(http_fixture, tmp_path):
    http_fixture.replies = [Reply(body=b"")]
    expected = hashlib.sha256(b"").hexdigest()
    result = run_download(http_fixture, tmp_path / "empty",
                          selected=source(expected_sha256=expected, expected_bytes=0))
    assert result.bytes_written == 0
    assert result.sha256 == expected
    assert (tmp_path / "empty").read_bytes() == b""


@pytest.mark.parametrize("selected", [
    source(expected_sha256="0" * 64),
    source(expected_bytes=len(PAYLOAD) + 1),
    source(expected_bytes=len(PAYLOAD) - 1),
])
def test_integrity_mismatch_never_publishes_partial_output(http_fixture, tmp_path, selected):
    with pytest.raises(DownloadError) as failure:
        run_download(http_fixture, tmp_path / "output", selected=selected)
    assert failure.value.code
    assert "private-fixture-value" not in str(failure.value)
    assert "signature=" not in str(failure.value)
    assert_clean(tmp_path)


@pytest.mark.parametrize("omit_length", [False, True])
def test_byte_budget_applies_to_declared_and_streamed_size(http_fixture, tmp_path, omit_length):
    http_fixture.replies = [Reply(omit_length=omit_length)]
    with pytest.raises(DownloadError):
        run_download(http_fixture, tmp_path / "output", selected=source(), settings=policy(max_bytes=8192))
    assert_clean(tmp_path)
    assert len(http_fixture.requests) == 1


def test_known_size_above_transfer_budget_is_rejected_before_contact(http_fixture, tmp_path):
    with pytest.raises(DownloadError) as failure:
        run_download(http_fixture, tmp_path / "output", settings=policy(max_transfer_bytes=len(PAYLOAD) - 1))
    assert failure.value.code == "transfer_limit"
    assert failure.value.transferred_bytes == 0
    assert http_fixture.requests == []
    assert_clean(tmp_path)


def test_unknown_length_stops_after_first_over_budget_raw_chunk(tmp_path):
    class Stream(httpx.AsyncByteStream):
        reads = 0
        closed = False

        async def __aiter__(self):
            for chunk in (b"abcd", b"efgh", b"ijkl"):
                self.reads += 1
                yield chunk

        async def aclose(self):
            self.closed = True

    stream = Stream()
    events = []
    transport = httpx.MockTransport(lambda request: httpx.Response(200, stream=stream))
    engine = DownloadEngine(policy(chunk_bytes=2, max_transfer_bytes=6), transport=transport)
    with pytest.raises(DownloadError) as failure:
        asyncio.run(engine.download(source(), tmp_path / "output", on_progress=events.append))
    assert failure.value.code == "transfer_limit"
    assert failure.value.transferred_bytes == 8
    assert stream.reads == 2 and stream.closed
    assert [(event.bytes_written, event.transferred_bytes) for event in events] == [(2, 4), (4, 4)]
    assert_clean(tmp_path)


@pytest.mark.parametrize("status", [401, 403, 404])
def test_permanent_errors_are_not_retried(http_fixture, tmp_path, status):
    http_fixture.replies = [Reply(status=status, body=b"upstream-private-detail"), Reply()]
    with pytest.raises(DownloadError) as failure:
        run_download(http_fixture, tmp_path / "output")
    assert len(http_fixture.requests) == 1
    assert "upstream-private-detail" not in str(failure.value)
    assert_clean(tmp_path)


@pytest.mark.parametrize("status", [429, 500, 502, 503, 504])
def test_transient_errors_have_bounded_retry_then_recover(http_fixture, tmp_path, status):
    http_fixture.replies = [Reply(status=status, body=b"retry", headers={"Retry-After": "0"}), Reply()]
    result = run_download(http_fixture, tmp_path / "output")
    assert result.attempts == 2
    assert result.transferred_bytes == len(PAYLOAD)
    assert (tmp_path / "output").read_bytes() == PAYLOAD
    assert len(http_fixture.requests) == 2


def test_retry_attempt_limit_is_enforced(http_fixture, tmp_path):
    http_fixture.replies = [Reply(status=503, body=b"unavailable")]
    with pytest.raises(DownloadError):
        run_download(http_fixture, tmp_path / "output", settings=policy(max_attempts=2))
    assert len(http_fixture.requests) == 2
    assert_clean(tmp_path)


def test_retry_after_above_budget_is_not_silently_shortened(http_fixture, tmp_path):
    http_fixture.replies = [Reply(status=429, body=b"slow down", headers={"Retry-After": "99999"}), Reply()]
    with pytest.raises(DownloadError):
        run_download(http_fixture, tmp_path / "output", settings=policy(max_retry_after=0.01))
    assert len(http_fixture.requests) == 1
    assert_clean(tmp_path)


def test_redirect_is_not_followed_even_to_same_host(http_fixture, tmp_path):
    http_fixture.replies = [Reply(status=302, body=b"", headers={"Location": "https://fixture.example/secret"}), Reply()]
    with pytest.raises(DownloadError):
        run_download(http_fixture, tmp_path / "output")
    assert len(http_fixture.requests) == 1
    assert_clean(tmp_path)


def test_compressed_response_is_rejected_without_publication(http_fixture, tmp_path):
    http_fixture.replies = [Reply(body=b"invalid compressed bytes", headers={"Content-Encoding": "gzip"})]
    with pytest.raises(DownloadError):
        run_download(http_fixture, tmp_path / "output")
    assert len(http_fixture.requests) == 1
    assert_clean(tmp_path)


def test_interrupted_stream_restarts_without_concatenating_partial_bytes(http_fixture, tmp_path):
    http_fixture.replies = [Reply(cut_after=16384), Reply()]
    result = run_download(http_fixture, tmp_path / "output", settings=policy(resume=False))
    assert result.attempts == 2
    assert result.resumed is False
    assert (tmp_path / "output").read_bytes() == PAYLOAD
    assert all("range" not in request["headers"] for request in http_fixture.requests)


def test_transfer_budget_retains_partial_chunk_cost_when_restart_is_blocked(http_fixture, tmp_path):
    cut = 123
    events = []
    http_fixture.replies = [Reply(cut_after=cut), Reply()]
    with pytest.raises(DownloadError) as failure:
        run_download(http_fixture, tmp_path / "output", progress=events.append,
                     settings=policy(resume=False, max_transfer_bytes=len(PAYLOAD)))
    assert failure.value.code == "transfer_limit"
    assert failure.value.transferred_bytes == cut
    assert events[-1].bytes_written == events[-1].transferred_bytes == cut
    assert len(http_fixture.requests) == 1
    assert_clean(tmp_path)


def test_restart_progress_keeps_counting_consumed_bytes(http_fixture, tmp_path):
    cut = 123
    events = []
    http_fixture.replies = [Reply(cut_after=cut), Reply()]
    destination = tmp_path / "output"
    result = run_download(http_fixture, destination, progress=events.append,
                          settings=policy(resume=False, max_transfer_bytes=len(PAYLOAD) + cut))
    assert result.attempts == 2
    assert result.transferred_bytes == len(PAYLOAD) + cut
    counts = [event.transferred_bytes for event in events]
    assert counts == sorted(counts)
    assert events[-1].bytes_written == len(PAYLOAD)
    assert counts[-1] == result.transferred_bytes
    assert destination.read_bytes() == PAYLOAD


def test_exhausted_truncated_transfer_cleans_all_files(http_fixture, tmp_path):
    http_fixture.replies = [Reply(cut_after=16384)]
    with pytest.raises(DownloadError) as failure:
        run_download(http_fixture, tmp_path / "output", settings=policy(max_attempts=2, resume=False))
    assert failure.value.code == "retry_exhausted"
    assert failure.value.transferred_bytes == 32768
    assert len(http_fixture.requests) == 2
    assert_clean(tmp_path)


def test_existing_destination_is_never_overwritten(http_fixture, tmp_path):
    destination = tmp_path / "output"
    destination.write_bytes(b"existing-user-work")
    with pytest.raises(DownloadError):
        run_download(http_fixture, destination)
    assert destination.read_bytes() == b"existing-user-work"
    assert list(tmp_path.iterdir()) == [destination]


def test_destination_created_during_transfer_is_never_overwritten(http_fixture, tmp_path):
    destination = tmp_path / "output"

    def competing_writer(event):
        if not destination.exists():
            destination.write_bytes(b"concurrent-user-work")

    with pytest.raises(DownloadError):
        run_download(http_fixture, destination, progress=competing_writer)
    assert destination.read_bytes() == b"concurrent-user-work"
    assert list(tmp_path.iterdir()) == [destination]


def test_cancellation_propagates_and_cleans_temporary_files(http_fixture, tmp_path):
    async def run():
        task = None

        def cancel_on_progress(event):
            if event.bytes_written:
                task.cancel()

        engine = DownloadEngine(policy=policy(), transport=http_fixture.transport())
        task = asyncio.create_task(engine.download(source(), tmp_path / "output", on_progress=cancel_on_progress))
        with pytest.raises(asyncio.CancelledError):
            await task

    asyncio.run(run())
    assert len(http_fixture.requests) == 1
    assert_clean(tmp_path)


def test_interrupted_stream_resumes_only_with_matching_strong_validator(http_fixture, tmp_path):
    offset = 123
    http_fixture.replies = [
        Reply(headers={"ETag": '"fixture-v1"'}, cut_after=offset),
        Reply(status=206, body=PAYLOAD[offset:], headers={
            "ETag": '"fixture-v1"',
            "Content-Range": f"bytes {offset}-{len(PAYLOAD) - 1}/{len(PAYLOAD)}",
        }),
    ]
    result = run_download(http_fixture, tmp_path / "output", settings=policy(max_transfer_bytes=len(PAYLOAD)))
    assert result.attempts == 2
    assert result.resumed is True
    assert result.bytes_written == len(PAYLOAD)
    assert result.transferred_bytes == len(PAYLOAD)
    assert result.sha256 == DIGEST
    assert (tmp_path / "output").read_bytes() == PAYLOAD
    assert http_fixture.requests[1]["headers"]["range"] == f"bytes={offset}-"
    assert http_fixture.requests[1]["headers"]["if-range"] == '"fixture-v1"'


@pytest.mark.parametrize("headers", [
    {},
    {"ETag": 'W/"fixture-v1"'},
    {"Last-Modified": "Wed, 21 Oct 2015 07:28:00 GMT"},
])
def test_absent_or_weak_validator_forces_clean_restart(http_fixture, tmp_path, headers):
    http_fixture.replies = [Reply(headers=headers, cut_after=16384), Reply()]
    result = run_download(http_fixture, tmp_path / "output")
    assert result.resumed is False
    assert result.attempts == 2
    assert "range" not in http_fixture.requests[1]["headers"]
    assert (tmp_path / "output").read_bytes() == PAYLOAD


def test_full_response_to_range_restarts_hash_and_output(http_fixture, tmp_path):
    http_fixture.replies = [Reply(headers={"ETag": '"fixture-v1"'}, cut_after=16384),
                            Reply(headers={"ETag": '"fixture-v2"'})]
    result = run_download(http_fixture, tmp_path / "output")
    assert result.bytes_written == len(PAYLOAD)
    assert result.sha256 == DIGEST
    assert (tmp_path / "output").read_bytes() == PAYLOAD
    assert "range" in http_fixture.requests[1]["headers"]


def test_ignored_range_cannot_exceed_remaining_body_budget(http_fixture, tmp_path):
    cut = 123
    http_fixture.replies = [Reply(headers={"ETag": '"fixture-v1"'}, cut_after=cut), Reply()]
    with pytest.raises(DownloadError) as failure:
        run_download(http_fixture, tmp_path / "output", settings=policy(max_transfer_bytes=len(PAYLOAD)))
    assert failure.value.code == "transfer_limit"
    assert failure.value.transferred_bytes == cut
    assert len(http_fixture.requests) == 2
    assert http_fixture.requests[1]["headers"]["range"] == f"bytes={cut}-"
    assert_clean(tmp_path)


@pytest.mark.parametrize("resume_reply", [
    Reply(status=206, body=PAYLOAD[16384:], headers={"ETag": '"wrong"',
          "Content-Range": f"bytes 16384-{len(PAYLOAD) - 1}/{len(PAYLOAD)}"}),
    Reply(status=206, body=PAYLOAD[16384:], headers={"ETag": '"fixture-v1"',
          "Content-Range": f"bytes 16383-{len(PAYLOAD) - 1}/{len(PAYLOAD)}"}),
    Reply(status=206, body=PAYLOAD[16384:], headers={"ETag": '"fixture-v1"',
          "Content-Range": f"bytes 16384-{len(PAYLOAD) - 1}/{len(PAYLOAD) + 1}"}),
    Reply(status=206, body=PAYLOAD[16384:], headers={"ETag": '"fixture-v1"'}),
    Reply(status=416, body=b"", headers={"Content-Range": f"bytes */{len(PAYLOAD)}"}),
])
def test_invalid_resume_response_fails_closed_and_cleans_output(http_fixture, tmp_path, resume_reply):
    http_fixture.replies = [Reply(headers={"ETag": '"fixture-v1"'}, cut_after=16384), resume_reply]
    with pytest.raises(DownloadError):
        run_download(http_fixture, tmp_path / "output", settings=policy(max_attempts=2))
    assert len(http_fixture.requests) == 2
    assert_clean(tmp_path)


def test_unsolicited_partial_response_cannot_be_published(http_fixture, tmp_path):
    http_fixture.replies = [Reply(status=206, body=PAYLOAD,
                            headers={"Content-Range": f"bytes 0-{len(PAYLOAD) - 1}/{len(PAYLOAD)}"})]
    with pytest.raises(DownloadError):
        run_download(http_fixture, tmp_path / "output")
    assert len(http_fixture.requests) == 1
    assert_clean(tmp_path)


def test_read_timeout_is_retried_only_within_attempt_budget(http_fixture, tmp_path):
    http_fixture.replies = [Reply(body_delay=0.1)]
    with pytest.raises(DownloadError):
        run_download(http_fixture, tmp_path / "output",
                     settings=policy(read_timeout=0.01, max_attempts=2))
    assert len(http_fixture.requests) == 2
    assert_clean(tmp_path)


def test_total_deadline_bounds_retries_and_cleans_output(http_fixture, tmp_path):
    http_fixture.replies = [Reply(body_delay=0.2)]
    started = time.monotonic()
    with pytest.raises(DownloadError):
        run_download(http_fixture, tmp_path / "output",
                     settings=policy(read_timeout=1, total_timeout=0.03, max_attempts=3))
    assert time.monotonic() - started < 1
    assert len(http_fixture.requests) == 1
    assert_clean(tmp_path)


@pytest.mark.parametrize("settings", [
    {"max_bytes": 0}, {"max_bytes": True}, {"max_attempts": 0}, {"max_attempts": 9},
    {"chunk_bytes": 0}, {"chunk_bytes": 1024 * 1024 + 1},
    {"connect_timeout": 0}, {"read_timeout": float("nan")},
    {"total_timeout": float("inf")}, {"total_timeout": True},
    {"backoff_base": -1}, {"backoff_base": 2, "backoff_max": 1},
    {"max_retry_after": -1}, {"resume": "true"},
    {"max_transfer_bytes": 0}, {"max_transfer_bytes": True}, {"max_transfer_bytes": 2**63},
])
def test_invalid_policy_configuration_is_rejected(settings):
    with pytest.raises(ValueError):
        TransferPolicy(**settings)


@pytest.mark.parametrize("expectation", [
    {"expected_sha256": "0" * 63}, {"expected_sha256": "A" * 64},
    {"expected_sha256": 17}, {"expected_bytes": -1}, {"expected_bytes": True},
    {"expected_bytes": 2**63},
])
def test_invalid_source_integrity_expectations_are_rejected(expectation):
    with pytest.raises(ValueError):
        source(**expectation)


def test_resumed_corruption_is_detected_before_publication(http_fixture, tmp_path):
    offset = 16384
    corrupt = PAYLOAD[offset:-1] + bytes([PAYLOAD[-1] ^ 1])
    http_fixture.replies = [
        Reply(headers={"ETag": '"fixture-v1"'}, cut_after=offset),
        Reply(status=206, body=corrupt, headers={"ETag": '"fixture-v1"',
            "Content-Range": f"bytes {offset}-{len(PAYLOAD) - 1}/{len(PAYLOAD)}"}),
    ]
    with pytest.raises(DownloadError) as failure:
        run_download(http_fixture, tmp_path / "output")
    assert failure.value.code == "integrity_mismatch"
    assert len(http_fixture.requests) == 2
    assert_clean(tmp_path)


def test_actual_connection_refusal_is_bounded_and_error_is_redacted(tmp_path):
    # A bound but non-listening local socket produces an actual TCP refusal;
    # there is no synthetic RequestError and no external network dependency.
    reserved = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    reserved.bind(("127.0.0.1", 0))

    class CountingTransport(FixtureTransport):
        calls = 0

        async def handle_async_request(self, request):
            self.calls += 1
            return await super().handle_async_request(request)

    transport = CountingTransport(reserved.getsockname()[1])

    async def run():
        engine = DownloadEngine(policy=policy(max_attempts=2), transport=transport)
        with pytest.raises(DownloadError) as failure:
            await engine.download(source(), tmp_path / "output")
        message = str(failure.value)
        assert failure.value.code == "retry_exhausted"
        assert "private-fixture-value" not in message
        assert "fixture.example" not in message
        assert "127.0.0.1" not in message

    try:
        asyncio.run(run())
    finally:
        reserved.close()
    assert transport.calls == 2
    assert_clean(tmp_path)


@pytest.mark.parametrize("declared_length", ["-1", "not-a-number", "9223372036854775808"])
def test_malformed_content_length_fails_bounded_and_never_publishes(http_fixture, tmp_path, declared_length):
    http_fixture.replies = [Reply(headers={"Content-Length": declared_length})]
    with pytest.raises(DownloadError):
        run_download(http_fixture, tmp_path / "output", settings=policy(max_attempts=2))
    assert 1 <= len(http_fixture.requests) <= 2
    assert_clean(tmp_path)


def test_retry_after_future_http_date_respects_wait_budget(http_fixture, tmp_path):
    future = format_datetime(datetime.now(timezone.utc) + timedelta(minutes=5), usegmt=True)
    http_fixture.replies = [Reply(status=503, body=b"busy", headers={"Retry-After": future}), Reply()]
    with pytest.raises(DownloadError) as failure:
        run_download(http_fixture, tmp_path / "output", settings=policy(max_retry_after=0.01))
    assert failure.value.code == "retry_after_limit"
    assert len(http_fixture.requests) == 1
    assert_clean(tmp_path)


def test_retry_after_past_http_date_allows_immediate_bounded_retry(http_fixture, tmp_path):
    http_fixture.replies = [Reply(status=503, body=b"busy",
                           headers={"Retry-After": "Sun, 06 Nov 1994 08:49:37 GMT"}), Reply()]
    result = run_download(http_fixture, tmp_path / "output", settings=policy(max_retry_after=0.01))
    assert result.attempts == 2
    assert (tmp_path / "output").read_bytes() == PAYLOAD
