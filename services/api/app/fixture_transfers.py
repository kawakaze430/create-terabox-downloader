"""Opt-in local transfer proof with a fixed source and no outbound network."""

import asyncio
from contextlib import asynccontextmanager
from dataclasses import dataclass, field
import hmac
import logging
from pathlib import Path
import re
import secrets
import shutil
import tempfile
import time
from typing import Literal

from fastapi import APIRouter, Depends, Request, Response
import httpx
from pydantic import BaseModel, ConfigDict, Field

from .download_engine import DownloadEngine, DownloadError, DownloadSource, TransferPolicy, TransferProgress


logger = logging.getLogger(__name__)
ROUTE_PREFIX = "/api/v1/fixture-transfers"
TOKEN_HEADER = "X-Transfer-Token"
SOURCE_ID = "42ff08467f614b4ca474723977354752"
SOURCE_HOST = "transfer-fixture.example"
SOURCE_URL = f"https://{SOURCE_HOST}/fixture"
FIXTURE_NAME = "transfer-fixture.bin"
FIXTURE_SIZE = 256 * 1024
FIXTURE_SHA256 = "2312394bd99545d9de131c24efb781e765ac1aec243f2ed9347597a793a415e9"
CHUNK_SIZE = 16 * 1024
CHUNK_DELAY = 0.08
MAX_RUNNING = 2
MAX_RETAINED = 8
JOB_TTL = 90
SWEEP_INTERVAL = 1
LOCAL_PEERS = {"127.0.0.1", "::1"}
LOCAL_HOST = r"(?:localhost|127\.0\.0\.1|\[::1\])(?::[0-9]{1,5})?"
LOCAL_ORIGIN = re.compile(rf"http://{LOCAL_HOST}")


class FixtureTransferError(Exception):
    def __init__(self, status: int, code: str, message: str):
        super().__init__(message)
        self.status = status
        self.code = code
        self.message = message


class CreateJobRequest(BaseModel):
    model_config = ConfigDict(extra="forbid", strict=True)
    source_id: str = Field(min_length=1, max_length=128)


class FixtureStream(httpx.AsyncByteStream):
    async def __aiter__(self):
        chunk = bytes(range(256)) * (CHUNK_SIZE // 256)
        for _ in range(FIXTURE_SIZE // CHUNK_SIZE):
            await asyncio.sleep(CHUNK_DELAY)
            yield chunk


class FixtureTransport(httpx.AsyncBaseTransport):
    async def handle_async_request(self, request: httpx.Request) -> httpx.Response:
        if request.method != "GET" or str(request.url) != SOURCE_URL:
            return httpx.Response(404)
        return httpx.Response(
            200,
            headers={"Content-Length": str(FIXTURE_SIZE)},
            stream=FixtureStream(),
        )


@dataclass
class FixtureJob:
    id: str
    token: str = field(repr=False)
    path: Path = field(repr=False)
    state: Literal["queued", "running", "completed", "cancelled", "failed"] = "queued"
    bytes_written: int = 0
    sha256: str | None = None
    expires_at: float | None = None
    task: asyncio.Task | None = field(default=None, repr=False)

    def snapshot(self):
        return {
            "id": self.id, "state": self.state, "bytes_written": self.bytes_written,
            "total_bytes": FIXTURE_SIZE, "sha256": self.sha256,
        }

    def update_progress(self, progress: TransferProgress):
        self.bytes_written = progress.bytes_written


class FixtureTransfers:
    """Per-process store. Only an owning job capability may read or cancel it."""

    def __init__(self, allowed_origins: list[str]):
        self.allowed_origins = frozenset(origin for origin in allowed_origins if LOCAL_ORIGIN.fullmatch(origin))
        self.directory: Path | None = None
        self.jobs: dict[str, FixtureJob] = {}

    @asynccontextmanager
    async def lifespan(self, _app):
        with tempfile.TemporaryDirectory(prefix="terabox-fixture-") as directory:
            self.directory = Path(directory)
            sweeper = asyncio.create_task(self.sweep())
            try:
                yield
            finally:
                tasks = [sweeper, *(job.task for job in self.jobs.values() if job.task is not None)]
                for task in tasks:
                    task.cancel()
                await asyncio.gather(*tasks, return_exceptions=True)
                self.jobs.clear()
                self.directory = None

    def expire(self):
        now = time.monotonic()
        for job in tuple(self.jobs.values()):
            if job.expires_at is not None and job.expires_at <= now:
                try:
                    shutil.rmtree(job.path.parent)
                except FileNotFoundError:
                    pass
                except OSError:
                    # Keep counting an expired file until it can be removed.
                    continue
                del self.jobs[job.id]

    async def sweep(self):
        while True:
            await asyncio.sleep(SWEEP_INTERVAL)
            self.expire()

    async def require_local_request(self, request: Request):
        origin = request.headers.get("origin")
        if (not request.client or request.client.host not in LOCAL_PEERS
                or not re.fullmatch(LOCAL_HOST, request.headers.get("host", "").lower())
                or (origin is not None and origin not in self.allowed_origins)):
            raise FixtureTransferError(404, "FIXTURE_NOT_FOUND", "Local transfer fixture not found.")

    async def run(self, job: FixtureJob):
        job.state = "running"
        try:
            engine = DownloadEngine(
                TransferPolicy(max_bytes=FIXTURE_SIZE, chunk_bytes=CHUNK_SIZE, max_attempts=1, total_timeout=10),
                transport=FixtureTransport(),
            )
            source = DownloadSource(
                SOURCE_URL, frozenset({SOURCE_HOST}), expected_sha256=FIXTURE_SHA256,
                expected_bytes=FIXTURE_SIZE,
            )
            result = await engine.download(source, job.path, on_progress=job.update_progress)
            job.bytes_written = result.bytes_written
            job.sha256 = result.sha256
            job.state = "completed"
        except asyncio.CancelledError:
            job.state = "cancelled"
            raise
        except (DownloadError, OSError):
            job.state = "failed"
        except Exception as exc:
            # A detached task must terminate with a public state even when an
            # unexpected exception occurs. Logs omit paths, tokens and URLs.
            logger.error("Unexpected local transfer failure (%s).", type(exc).__name__)
            job.state = "failed"
        finally:
            job.expires_at = time.monotonic() + JOB_TTL

    def get_job(self, request: Request, job_id: str) -> FixtureJob:
        self.expire()
        job = self.jobs.get(job_id)
        token = request.headers.get(TOKEN_HEADER, "")
        if (job is None or (job.expires_at is not None and job.expires_at <= time.monotonic())
                or len(token) != len(job.token) or not token.isascii() or not hmac.compare_digest(job.token, token)):
            raise FixtureTransferError(404, "FIXTURE_JOB_NOT_FOUND", "Transfer job not found.")
        return job

    def router(self):
        router = APIRouter(prefix=ROUTE_PREFIX, dependencies=[Depends(self.require_local_request)])

        @router.get("/source")
        async def get_source():
            return {"source_id": SOURCE_ID}

        @router.post("/jobs", status_code=201)
        async def create_job(body: CreateJobRequest):
            if body.source_id != SOURCE_ID:
                raise FixtureTransferError(404, "FIXTURE_SOURCE_NOT_FOUND", "Transfer source not found.")
            self.expire()
            if (self.directory is None or len(self.jobs) >= MAX_RETAINED
                    or sum(job.state in ("queued", "running") for job in self.jobs.values()) >= MAX_RUNNING):
                raise FixtureTransferError(503, "FIXTURE_BUSY", "The local transfer fixture is busy. Try again shortly.")
            job_id = secrets.token_hex(16)
            directory = self.directory / job_id
            try:
                directory.mkdir(mode=0o700)
            except OSError:
                raise FixtureTransferError(503, "FIXTURE_BUSY", "The local transfer fixture is busy. Try again shortly.") from None
            job = FixtureJob(job_id, secrets.token_hex(32), directory / FIXTURE_NAME)
            self.jobs[job_id] = job
            job.task = asyncio.create_task(self.run(job))
            return {"token": job.token, **job.snapshot()}

        @router.get("/jobs/{job_id}")
        async def get_status(request: Request, job_id: str):
            return self.get_job(request, job_id).snapshot()

        @router.post("/jobs/{job_id}/cancel")
        async def cancel_job(request: Request, job_id: str):
            job = self.get_job(request, job_id)
            if job.state in ("queued", "running") and job.task is not None:
                job.state = "cancelled"
                job.expires_at = time.monotonic() + JOB_TTL
                job.task.cancel()
                await asyncio.gather(job.task, return_exceptions=True)
            return job.snapshot()

        @router.get("/jobs/{job_id}/file")
        async def get_file(request: Request, job_id: str):
            job = self.get_job(request, job_id)
            if job.state != "completed":
                raise FixtureTransferError(409, "FIXTURE_FILE_UNAVAILABLE", "The transfer file is unavailable.")
            # The fixture is always exactly 256 KiB. Read it before awaiting a
            # response so expiration cannot race the opening of the file.
            try:
                with job.path.open("rb") as output:
                    body = output.read(FIXTURE_SIZE + 1)
            except OSError:
                body = b""
            if len(body) != FIXTURE_SIZE:
                raise FixtureTransferError(409, "FIXTURE_FILE_UNAVAILABLE", "The transfer file is unavailable.")
            return Response(body, media_type="application/octet-stream", headers={
                "Content-Disposition": f'attachment; filename="{FIXTURE_NAME}"',
            })

        return router
