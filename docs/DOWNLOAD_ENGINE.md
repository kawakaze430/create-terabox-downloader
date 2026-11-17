# Source-independent download engine

## Goal and boundaries

Transfer bytes from a permitted source independently of its metadata/authentication adapter. No OAuth or GPT inference is needed by the transfer algorithm. The existing TeraBox official client remains an optional operator-only candidate; a public share URL is not automatically a safe byte source.

The generic engine lives inside the existing Python service. Its input is a trusted source descriptor: a secret/repr-hidden HTTPS URL, exact allowed destination hosts, optional independently known size and SHA-256. Production requests reuse checked-IP TLS transport in `egress.py`. An explicit injected transport supports controlled socket fixtures; production host/DNS checks are not disabled to test localhost.

There will be no anonymous arbitrary-URL proxy endpoint. The internal library/CLI accepts operator-approved sources; connecting a visitor workflow requires an adapter to resolve and authorize file IDs, resource limits and safe delivery ownership first.

## Implementation plan

1. Single streamed GET with identity encoding and fixed-size reads; connect/read/total deadlines and maximum bytes.
2. Bound retry attempts for connection/read errors and transient statuses; exponential full jitter; respect bounded Retry-After without retrying earlier than requested.
3. Independently check size/digest, reject truncation/encoding/incorrect status, keep partial files private, publish without overwriting existing destinations, clean on failure/cancellation.
4. Recover interrupted transfers with a byte range only after receiving a known total size and strong ETag. Validate 206 Content-Range, exact remainder size, unchanged ETag and final digest. Range ignored with 200 resets safely; 416/malformed/version mismatch fails closed. Resume without a strong validator is not claimed.
5. Evaluate parallel ranges/adaptive scheduling only after a benchmark demonstrates value within source limits. These are not required to make a reliable first engine and remain unimplemented unless explicitly verified.

Progress reports actual bytes written, not fabricated percentages. Retry/restart may reset observed progress. Completion means the entire expected stream was validated and atomically published. A digest calculated without a trusted expected digest detects no independent corruption by itself; report that distinction.

## Planned evidence

Controlled local HTTP server fixtures cover correct small/large files, transient/permanent statuses, retry exhaustion, truncated/wrong lengths, oversized/encoded responses, timeout, cancellation, version/range errors, checksum mismatch and temporary-file cleanup. Ordinary CI must not depend on third-party access or secrets. Benchmarks must record fixture size, delays, repetitions, concurrency, byte counts and correctness; do not claim internet speed improvements from loopback measurements.

This file will be updated with actual implemented commands/results at each tested checkpoint. Until then the algorithm list above is design, not completion evidence.
