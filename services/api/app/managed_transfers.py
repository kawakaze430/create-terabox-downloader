"""Single-worker transfers from an operator-owned HTTPS source registry."""

import asyncio
from contextlib import asynccontextmanager
from dataclasses import dataclass, field
import hashlib
import hmac
import json
import logging
import os
from pathlib import Path
import re
import secrets
import shutil
import stat
import time
from typing import BinaryIO, Literal
from urllib.parse import urlsplit

from fastapi import APIRouter, Depends, Request, Response
from fastapi.responses import StreamingResponse
from pydantic import BaseModel, ConfigDict, Field

from .download_engine import DownloadEngine, DownloadError, DownloadSource, TransferPolicy, TransferProgress
from .egress import validate_hosts


logger = logging.getLogger(__name__)
MANAGED_PREFIX = "/api/v1/transfers"
MAX_FILE_BYTES = 16 * 1024 * 1024
MAX_REGISTRY_BYTES = 64 * 1024
SESSION_TTL = 900
JOB_TTL = 180
SWEEP_INTERVAL = 2
DELIVERY_TIMEOUT = 120
MAX_SESSIONS = 16
MAX_RUNNING = 2
MAX_JOBS = 8
MAX_SESSION_JOBS = 2
MAX_SESSION_STARTS = 8
MAX_DELIVERIES = 4
CHUNK_BYTES = 64 * 1024
ID_PATTERN = r"^[A-Za-z0-9_-]{1,128}$"
KEY_PATTERN = r"[A-Za-z0-9_-]{32,128}"
TOKEN_PATTERN = re.compile(r"[A-Za-z0-9_-]{43}")
JOB_DIRECTORY = re.compile(r"job-[0-9a-f]{32}")
LOCAL_HOST = re.compile(r"(?:localhost|127\.0\.0\.1|\[::1\])(?::[0-9]{1,5})?")
LOCAL_PEERS = {"127.0.0.1", "::1"}


class ManagedTransferError(Exception):
    def __init__(self, status: int, code: str, message: str):
        super().__init__(message)
        self.status = status
        self.code = code
        self.message = message


class StrictObject(BaseModel):
    model_config = ConfigDict(extra="forbid", strict=True)


class SessionRequest(StrictObject):
    access_key: str = Field(min_length=32, max_length=128)


class JobRequest(StrictObject):
    source_id: str = Field(pattern=ID_PATTERN)


class RegisteredSource(JobRequest):
    name: str = Field(pattern=r"^[A-Za-z0-9][A-Za-z0-9._ -]{0,127}$")
    url: str = Field(min_length=1, max_length=8192, repr=False)
    size_bytes: int = Field(ge=0, le=MAX_FILE_BYTES)
    sha256: str = Field(pattern=r"^[0-9a-f]{64}$")


class Registry(StrictObject):
    allowed_hosts: list[str] = Field(min_length=1, max_length=32)
    sources: list[RegisteredSource] = Field(min_length=1, max_length=32)


@dataclass(frozen=True)
class Source:
    source_id: str
    name: str
    download: DownloadSource = field(repr=False)

    def public(self):
        return {"source_id": self.source_id, "name": self.name,
                "size_bytes": self.download.expected_bytes, "sha256": self.download.expected_sha256}


def unique_json_object(pairs):
    result = {}
    for key, value in pairs:
        if key in result:
            raise ValueError("Duplicate registry field.")
        result[key] = value
    return result


def load_registry(path: Path) -> dict[str, Source]:
    if not path.is_absolute():
        raise ValueError("Managed transfer registry path must be absolute.")
    try:
        descriptor = os.open(path, os.O_RDONLY | os.O_NOFOLLOW | os.O_NONBLOCK)
        with os.fdopen(descriptor, "rb") as registry_file:
            details = os.fstat(registry_file.fileno())
            if (not stat.S_ISREG(details.st_mode) or details.st_uid != os.geteuid()
                    or details.st_mode & 0o077 or details.st_size > MAX_REGISTRY_BYTES):
                raise ValueError()
            content = registry_file.read(MAX_REGISTRY_BYTES + 1)
        if len(content) > MAX_REGISTRY_BYTES:
            raise ValueError()
        registry = Registry.model_validate(json.loads(content, object_pairs_hook=unique_json_object))
        hosts = validate_hosts(registry.allowed_hosts)
        if len(hosts) != len(registry.allowed_hosts):
            raise ValueError()
        sources = {}
        for item in registry.sources:
            if item.source_id in sources or item.name.rstrip(" .") != item.name:
                raise ValueError()
            download = DownloadSource(item.url, hosts, item.sha256, item.size_bytes)
            sources[item.source_id] = Source(item.source_id, item.name, download)
        return sources
    except (OSError, ValueError, RecursionError):
        raise ValueError("Managed transfer registry is unsafe or invalid.") from None


def exact_origin(value: str) -> bool:
    if not re.fullmatch(r"https?://[A-Za-z0-9.\[\]:-]+", value):
        return False
    try:
        parsed = urlsplit(value)
        if parsed.port is not None and parsed.port == 0:
            return False
    except ValueError:
        return False
    return bool(parsed.hostname and (parsed.scheme == "https" or LOCAL_HOST.fullmatch(parsed.netloc)))


def require_private_directory(path: Path):
    details = path.lstat()
    if (not stat.S_ISDIR(details.st_mode) or details.st_uid != os.geteuid()
            or stat.S_IMODE(details.st_mode) != 0o700 or path.resolve(strict=True) != path):
        raise ValueError("Managed transfer storage must be a private real directory.")
    for parent in path.parents:
        if os.statvfs(parent).f_flag & os.ST_RDONLY:
            continue
        details = parent.stat()
        if details.st_uid not in (0, os.geteuid()) or (details.st_mode & 0o022 and not details.st_mode & stat.S_ISVTX):
            raise ValueError("Managed transfer storage has an untrusted parent directory.")


@dataclass
class Session:
    expires_at: float
    starts: int = 0


@dataclass
class Job:
    id: str
    owner: bytes = field(repr=False)
    source: Source
    path: Path = field(repr=False)
    state: Literal["queued", "running", "completed", "cancelled", "failed"] = "queued"
    bytes_written: int = 0
    sha256: str | None = None
    expires_at: float | None = None
    delivering: bool = False
    task: asyncio.Task | None = field(default=None, repr=False)

    def snapshot(self):
        return {"id": self.id, "state": self.state, "bytes_written": self.bytes_written,
                "total_bytes": self.source.download.expected_bytes, "sha256": self.sha256}

    def update_progress(self, progress: TransferProgress):
        self.bytes_written = progress.bytes_written


class FileDelivery(StreamingResponse):
    def __init__(self, job: Job, file: BinaryIO):
        self.job = job
        self.file = file
        super().__init__(self.chunks(), media_type="application/octet-stream", headers={
            "Content-Disposition": f'attachment; filename="{job.source.name}"',
            "Content-Length": str(job.source.download.expected_bytes),
        })

    async def chunks(self):
        while chunk := self.file.read(CHUNK_BYTES):
            yield chunk
            await asyncio.sleep(0)

    async def __call__(self, scope, receive, send):
        try:
            async with asyncio.timeout(DELIVERY_TIMEOUT):
                await super().__call__(scope, receive, send)
        finally:
            self.file.close()
            self.job.delivering = False


class ManagedTransfers:
    def __init__(self, registry: dict[str, Source], storage: Path, access_key: str,
                 origins: list[str], *, engine_factory=None):
        if not storage.is_absolute() or not re.fullmatch(KEY_PATTERN, access_key):
            raise ValueError("Managed transfers require an absolute storage path and a strong access key.")
        if any(not exact_origin(origin) for origin in origins):
            raise ValueError("Managed transfers require exact HTTPS or local development client origins.")
        self.registry = registry
        self.storage = storage
        self.key_hash = hashlib.sha256(access_key.encode("ascii")).digest()
        self.origins = frozenset(origins)
        self.engine_factory = engine_factory or DownloadEngine
        self.directory: Path | None = None
        self.sessions: dict[bytes, Session] = {}
        self.jobs: dict[str, Job] = {}

    @classmethod
    def from_environment(cls, origins: list[str]):
        registry_path = os.getenv("TRANSFER_REGISTRY_PATH")
        if not registry_path:
            return None
        if os.name != "posix" or not hasattr(os, "O_NOFOLLOW"):
            raise RuntimeError("Managed transfers require POSIX private storage support.")
        return cls(load_registry(Path(registry_path)), Path(os.getenv("TRANSFER_STORAGE_DIR", "")),
                   os.getenv("TRANSFER_ACCESS_KEY", ""), origins)

    @asynccontextmanager
    async def lifespan(self, _app):
        try:
            import fcntl
        except ImportError:
            raise RuntimeError("Managed transfer storage requires POSIX advisory locks.") from None
        lock_path = self.storage / ".transfer-worker.lock"
        try:
            require_private_directory(self.storage)
            descriptor = os.open(lock_path, os.O_RDWR | os.O_CREAT | os.O_NOFOLLOW | os.O_NONBLOCK, 0o600)
        except OSError:
            raise ValueError("Managed transfer storage lock is unavailable.") from None
        try:
            details = os.fstat(descriptor)
            if not stat.S_ISREG(details.st_mode) or details.st_uid != os.geteuid() or details.st_mode & 0o077:
                raise ValueError("Managed transfer storage lock is invalid.")
            try:
                fcntl.flock(descriptor, fcntl.LOCK_EX | fcntl.LOCK_NB)
            except OSError:
                raise RuntimeError("Managed transfer storage requires one worker with an exclusive lock.") from None
            directory = self.storage / "managed-transfers-v1"
            directory.mkdir(mode=0o700, exist_ok=True)
            require_private_directory(directory)
            entries = tuple(directory.iterdir())
            for entry in entries:
                if not JOB_DIRECTORY.fullmatch(entry.name):
                    raise ValueError("Managed transfer storage contains an unexpected entry.")
                require_private_directory(entry)
            for entry in entries:
                shutil.rmtree(entry)
            self.directory = directory
            sweeper = asyncio.create_task(self.sweep())
            try:
                yield
            finally:
                tasks = [sweeper, *(job.task for job in self.jobs.values() if job.task is not None)]
                for task in tasks:
                    task.cancel()
                await asyncio.gather(*tasks, return_exceptions=True)
                self.sessions.clear()
                self.expire()
                self.jobs.clear()
                self.directory = None
        except OSError:
            raise RuntimeError("Managed transfer storage operation failed.") from None
        finally:
            os.close(descriptor)

    def expire(self):
        now = time.monotonic()
        for owner, session in tuple(self.sessions.items()):
            if session.expires_at <= now:
                del self.sessions[owner]
        for job in tuple(self.jobs.values()):
            expired = job.owner not in self.sessions or (job.expires_at is not None and job.expires_at <= now)
            if not expired:
                continue
            if job.task is not None and not job.task.done():
                if not job.task.cancelling():
                    job.task.cancel()
                continue
            if job.delivering:
                continue
            try:
                shutil.rmtree(job.path.parent)
            except FileNotFoundError:
                pass
            except OSError:
                # An expired job with a remaining file still consumes its slot.
                continue
            del self.jobs[job.id]

    async def sweep(self):
        while True:
            await asyncio.sleep(SWEEP_INTERVAL)
            self.expire()

    async def require_transport(self, request: Request):
        local = (request.client and request.client.host in LOCAL_PEERS
                 and LOCAL_HOST.fullmatch(request.headers.get("host", "").lower()))
        if request.scope["scheme"] != "https" and not local:
            raise ManagedTransferError(403, "TRANSFER_HTTPS_REQUIRED", "An HTTPS connection is required.")
        origin = request.headers.get("origin")
        if origin is not None and origin not in self.origins:
            raise ManagedTransferError(403, "TRANSFER_ORIGIN_DENIED", "Transfer origin is not allowed.")

    async def require_session(self, request: Request):
        scheme, _, token = request.headers.get("authorization", "").partition(" ")
        if scheme.lower() == "bearer" and TOKEN_PATTERN.fullmatch(token):
            owner = hashlib.sha256(token.encode("ascii")).digest()
            session = self.sessions.get(owner)
            if session is not None and session.expires_at > time.monotonic():
                return owner
        raise ManagedTransferError(401, "TRANSFER_SESSION_REQUIRED", "Start a transfer session to continue.")

    def find_job(self, job_id: str, owner: bytes) -> Job:
        job = self.jobs.get(job_id)
        if (job is None or not hmac.compare_digest(job.owner, owner)
                or (job.expires_at is not None and job.expires_at <= time.monotonic())):
            raise ManagedTransferError(404, "TRANSFER_JOB_NOT_FOUND", "Transfer job not found.")
        return job

    async def run(self, job: Job):
        job.state = "running"
        try:
            size = job.source.download.expected_bytes
            if size is None:
                raise ValueError("Registered transfer has no expected size.")
            policy = TransferPolicy(max_bytes=max(1, size), max_transfer_bytes=max(1, size * 2),
                                    max_attempts=2, total_timeout=180)
            result = await self.engine_factory(policy).download(job.source.download, job.path, on_progress=job.update_progress)
            job.bytes_written = result.bytes_written
            job.sha256 = result.sha256
            job.state = "completed"
        except asyncio.CancelledError:
            job.state = "cancelled"
            raise
        except (DownloadError, OSError):
            job.state = "failed"
        except Exception as exc:
            logger.error("Unexpected managed transfer failure (%s).", type(exc).__name__)
            job.state = "failed"
        finally:
            job.expires_at = time.monotonic() + JOB_TTL

    def router(self):
        router = APIRouter(prefix=MANAGED_PREFIX, dependencies=[Depends(self.require_transport)])

        @router.post("/session")
        async def create_session(body: SessionRequest):
            if (not re.fullmatch(KEY_PATTERN, body.access_key)
                    or not hmac.compare_digest(self.key_hash, hashlib.sha256(body.access_key.encode("ascii")).digest())):
                raise ManagedTransferError(401, "TRANSFER_ACCESS_DENIED", "The transfer access key is invalid.")
            self.expire()
            if self.directory is None or len(self.sessions) >= MAX_SESSIONS:
                raise ManagedTransferError(503, "TRANSFER_BUSY", "Transfer service is at capacity. Try again shortly.")
            token = secrets.token_urlsafe(32)
            self.sessions[hashlib.sha256(token.encode("ascii")).digest()] = Session(time.monotonic() + SESSION_TTL)
            return {"token": token, "expires_in": SESSION_TTL}

        @router.post("/session/logout", status_code=204)
        async def logout(_body: StrictObject, owner: bytes = Depends(self.require_session)):
            self.sessions.pop(owner, None)
            self.expire()
            return Response(status_code=204)

        @router.get("/sources", dependencies=[Depends(self.require_session)])
        async def sources():
            return {"sources": [source.public() for source in self.registry.values()]}

        @router.post("/jobs", status_code=201)
        async def create_job(body: JobRequest, owner: bytes = Depends(self.require_session)):
            source = self.registry.get(body.source_id)
            if source is None:
                raise ManagedTransferError(404, "TRANSFER_SOURCE_NOT_FOUND", "Transfer source not found.")
            self.expire()
            session = self.sessions.get(owner)
            if session is None:
                raise ManagedTransferError(401, "TRANSFER_SESSION_REQUIRED", "Start a transfer session to continue.")
            own_jobs = [job for job in self.jobs.values() if job.owner == owner]
            running = [job for job in self.jobs.values() if job.task is not None and not job.task.done()]
            if (session.starts >= MAX_SESSION_STARTS or len(own_jobs) >= MAX_SESSION_JOBS
                    or any(job.owner == owner for job in running)):
                raise ManagedTransferError(429, "TRANSFER_SESSION_LIMIT", "This transfer session is at capacity.")
            if self.directory is None or len(self.jobs) >= MAX_JOBS or len(running) >= MAX_RUNNING:
                raise ManagedTransferError(503, "TRANSFER_BUSY", "Transfer service is at capacity. Try again shortly.")
            job_id = secrets.token_hex(16)
            directory = self.directory / f"job-{job_id}"
            try:
                directory.mkdir(mode=0o700)
            except OSError:
                raise ManagedTransferError(503, "TRANSFER_BUSY", "Transfer storage is unavailable.") from None
            job = Job(job_id, owner, source, directory / "result")
            self.jobs[job_id] = job
            session.starts += 1
            job.task = asyncio.create_task(self.run(job))
            return job.snapshot()

        @router.get("/jobs/{job_id}")
        async def status(job_id: str, owner: bytes = Depends(self.require_session)):
            return self.find_job(job_id, owner).snapshot()

        @router.post("/jobs/{job_id}/cancel")
        async def cancel(job_id: str, _body: StrictObject, owner: bytes = Depends(self.require_session)):
            job = self.find_job(job_id, owner)
            if job.state in ("queued", "running") and job.task is not None:
                job.state = "cancelled"
                job.expires_at = time.monotonic() + JOB_TTL
                job.task.cancel()
                await asyncio.gather(job.task, return_exceptions=True)
            return job.snapshot()

        @router.get("/jobs/{job_id}/file")
        async def file(job_id: str, owner: bytes = Depends(self.require_session)):
            job = self.find_job(job_id, owner)
            unavailable = ManagedTransferError(409, "TRANSFER_FILE_UNAVAILABLE", "The transfer file is unavailable.")
            if job.state != "completed":
                raise unavailable
            if job.delivering or sum(job.delivering for job in self.jobs.values()) >= MAX_DELIVERIES:
                raise ManagedTransferError(503, "TRANSFER_BUSY", "File delivery is at capacity. Try again shortly.")
            try:
                output = os.fdopen(os.open(job.path, os.O_RDONLY | os.O_NOFOLLOW | os.O_NONBLOCK), "rb")
            except OSError:
                raise unavailable from None
            try:
                details = os.fstat(output.fileno())
                if not stat.S_ISREG(details.st_mode) or details.st_size != job.source.download.expected_bytes:
                    raise unavailable
            except (OSError, ManagedTransferError):
                output.close()
                raise unavailable from None
            job.delivering = True
            return FileDelivery(job, output)

        return router
