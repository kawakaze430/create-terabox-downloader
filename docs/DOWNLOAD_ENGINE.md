# Source-independent download engine

## Goal and boundaries

Transfer bytes from a permitted source independently of its metadata/authentication adapter. No OAuth or GPT inference is needed by the transfer algorithm. The existing TeraBox official client remains an optional operator-only candidate; a public share URL is not automatically a safe byte source.

The generic engine lives inside the existing Python service. Its input is a trusted source descriptor: a secret/repr-hidden HTTPS URL, exact allowed destination hosts, optional independently known size and SHA-256. Production requests reuse checked-IP TLS transport in `egress.py`. An explicit injected transport supports controlled socket fixtures; production host/DNS checks are not disabled to test localhost.

There will be no anonymous arbitrary-URL proxy endpoint. The internal library/CLI accepts operator-approved sources; connecting a visitor workflow requires an adapter to resolve and authorize file IDs, resource limits and safe delivery ownership first.

## Implemented algorithms

1. Single streamed GET with identity encoding and fixed-size reads; connect/read/total deadlines and maximum bytes.
2. Bound retry attempts for connection/read errors and transient statuses; exponential full jitter; respect bounded Retry-After without retrying earlier than requested.
3. Independently check size/digest, reject truncation/encoding/incorrect status, keep partial files private, publish without overwriting existing destinations, clean on failure/cancellation.
4. Recover interrupted transfers with a byte range only after receiving a known total size and strong ETag. Validate 206 Content-Range, exact remainder size, unchanged ETag and final digest. Range ignored with 200 resets safely; 416/malformed/version mismatch fails closed. Resume without a strong validator is not claimed.
5. Parallel ranges/adaptive scheduling are **not implemented**. Evaluate only after controlled benchmarks demonstrate value within source limits. Fixed sequential recovery is deliberately the initial correct algorithm.

Progress reports actual bytes written, not fabricated percentages. Retry/restart may reset observed progress. Completion means the entire expected stream was validated and atomically published. A digest calculated without a trusted expected digest detects no independent corruption by itself; report that distinction.

## Verification and operation

Controlled local HTTP server fixtures cover correct small/large files, transient/permanent statuses, retry exhaustion, truncated/wrong lengths, oversized/encoded responses, timeout, cancellation, version/range errors, checksum mismatch and temporary-file cleanup. Ordinary CI must not depend on third-party access or secrets. Benchmarks must record fixture size, delays, repetitions, concurrency, byte counts and correctness; do not claim internet speed improvements from loopback measurements.

Current verification: 74 engine tests plus 3 CLI tests passed, including real local HTTP sockets. The complete API suite passed 250 tests (the previous 173 plus those 77); pip check passed. Existing Starlette/httpx testclient deprecation remains. No new package dependency was added. The explicit fixture transport is not used by the production CLI.

```bash
# Root: independent focused tests (no TeraBox network access).
PYTHONPATH=services/api services/api/.venv/bin/python -m pytest -q \
  services/api/tests/test_download_engine.py services/api/tests/test_download_cli.py

# Operator: ENGINE_SOURCE_URL must already contain an authorized direct HTTPS
# file URL, supplied privately through the environment, not pasted into Git.
# Replace host/digest/size placeholders using your independently known file.
PYTHONPATH=services/api services/api/.venv/bin/python -m app.download_cli \
  /tmp/new-download.bin --host your-approved-source.example \
  --max-bytes 10485760 --expected-bytes 12345 --sha256 EXPECTED_LOWERCASE_DIGEST
```

The CLI prints sanitized JSON statistics only. Exit 0 means validated stream publication, 1 a transfer failure, 2 invalid configuration and 130 interruption. A SHA-256 is always computed; `integrity_verified` is true only when a trusted expected digest matched. `bytes_written` is the final file length; `transferred_bytes` counts body bytes yielded to the engine across attempts, including discarded retries. It is not a wire/TLS bandwidth counter.

Progress callbacks get `bytes_written`, `total_bytes` (possibly unknown), and `attempt`; a full restart resets progress. Paths and callbacks are trusted internal inputs. No browser progress endpoint, public job service or source refresh callback exists yet.

Limits: resume is within one invocation only, not durable cross-process resume. Only strong ETag plus known total supports recovery; ignored Range restarts from zero. A 416, wrong interval/size or changed 206 validator fails closed. Permanent authorization failures are not retried; refreshing expired source URLs belongs to an authorized adapter. Retry count is capped at eight, defaults to three; output max bytes is per attempt/file, while total network consumption is also bounded by attempts and total time. Disk writes are fixed-size synchronous operations; cooperative timeouts cannot interrupt blocked filesystem I/O. Atomic no-clobber publication uses a same-directory hard link, requiring filesystem support, and does not promise crash-durable directory metadata. Files remain mode 0600. Do not expose arbitrary destination paths to visitors.

TeraBox's public provider remains disabled; this engine does not turn share URLs into accessible bytes. Website/extension integration waits for an authorized source adapter and a properly scoped transfer workflow, rather than exposing a generic URL proxy.

## Controlled recovery benchmark — 17 November 2026

```bash
services/api/.venv/bin/python scripts/benchmark_download_engine.py --size-mib 4 --repeats 3
```

One loopback HTTP server, preallocated deterministic 4 MiB payload, 64 KiB chunks,
one connection/transfer at a time, injected fixture transport, no backoff delay.
One warmup excluded; interrupted scenarios close the first response after 512 KiB.
All nine measured transfers matched expected size and independent SHA-256. Raw
samples/limitations: [ENGINE_BENCHMARK_2026-11-17.json](ENGINE_BENCHMARK_2026-11-17.json).

| Scenario | Median elapsed | Body bytes across attempts | Attempts | Median traced Python peak |
| --- | --- | --- | --- | --- |
| Clean full stream | 0.044010 s | 4,194,304 | 1 | 831,555 bytes |
| Interrupted, restart | 0.044481 s | 4,718,592 | 2 | 923,814 bytes |
| Interrupted, safe resume | 0.045834 s | 4,194,304 | 2 | 948,484 bytes |

Resume avoided 524,288 retransmitted body bytes (11.11% of this restart scenario's
body traffic). It did **not** show a speed advantage in this run. These are local
observations with uncontrolled OS/filesystem caches, not production throughput
or TeraBox performance. Tracing measures process Python allocations including
server threads, excludes preallocated payload/imports, and is not RSS. Body
counters exclude protocol/TLS overhead and are not acknowledged wire bytes.
Parallel ranges/adaptive concurrency were not benchmarked because they are not
implemented. The current evidence supports byte-efficient correct recovery,
not a claim that more concurrency will improve performance.
