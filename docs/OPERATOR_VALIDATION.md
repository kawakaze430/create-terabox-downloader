# Operator validation: prove the first real download

**Status: implemented and verified with offline fixtures only. No live TeraBox
metadata, OAuth, or file transfer has passed. The public provider is disabled.**

This command prepares the G1 acceptance test. It does not enable downloads for
website visitors, collect user passwords, publish a service or share credentials.

## Prerequisites

Obtain approved partner credentials and an operator-consented access token using
the [official integration process](OFFICIAL_OPEN_PLATFORM.md). Confirm the
permitted external-share scopes and regional API/CDN hostnames with TeraBox.
Create one small non-sensitive public share containing a file you own. Keep the
original file to calculate its SHA-256 checksum and identify the file ID.

Populate the empty settings documented in `services/api/.env.example` through
your shell's environment or a deployment secret manager. The CLI does not load
`.env` automatically. Keep real values outside Git, CI output and chat. The
`TERABOX_PARTNER_APPROVED=true` flag records your confirmation; it cannot obtain
or establish approval on its own.

## Commands

From the repository root with the API virtual environment active:

```bash
# Offline: reports missing/invalid variable names, never their values.
PYTHONPATH=services/api python -m app.preflight

# Explicit network opt-in: one authorized small file, at most 10 MiB.
PYTHONPATH=services/api python -m app.preflight --live
```

Exit codes: `0` = configuration ready (offline) or complete matching file (live);
`2` = missing/invalid configuration; `1` = live probe failed. **Offline success is
not a live test.** Successful live output includes `live_verified: true`, the
file count and verified byte count; no file contents, URLs or tokens are printed
or persisted. A success remains limited to that one fixture, scope and account.
Record the date, commit SHA and sanitized JSON result in the implementation log.

The probe:

1. Gets regional API information using the existing OAuth client.
2. Calls the official share metadata endpoint and checks the selected file ID.
3. Requests that file's link only, requiring an exact operator-approved CDN host.
4. Reads within the byte/time budget and compares the entire SHA-256 digest and
   advertised size. An HTTP handoff alone is never reported as completion.

Network protections include HTTPS certificate verification with the original
hostname, exact host allowlists, public-address DNS checks, connections pinned
to the checked IP, no redirects, identity-only responses, finite streaming
limits/timeouts, and separate API/CDN clients to prevent cookie/token forwarding.
No implicit proxy is used; run on an approved host with direct outbound access.
The application still needs deployment-level egress and aggregate rate limits.

## Deliberate compatibility limits

This is an operator-only candidate client based on
[TeraBox's official documentation](https://www.terabox.com/integrations/docs/chinese).
Only `/s/1...` public, unprotected shares and one root-level file are probed.
Password verification, recursive folders, preview/qualities, ZIP and per-user
public authorization remain unimplemented. Unknown response formats fail closed.

The documentation's download parameter table says `access_token`, while a curl
example says `access_tokens`; the client uses the table without automatically
retrying alternative protocols. The response table says `fid_id`, while the
sample uses `fs_id`; both are accepted only when they match the selected file.
These inconsistencies and the empty password/session parameters for public shares
must be checked with partner-approved live evidence. Do not hide a failure by
switching to scraped cookies, borrowed sessions or third-party proxies.

After a successful live probe, design and verify per-user consent, session/token
isolation, expiry/refresh, actual regional scopes and the public download handoff
before connecting `OfficialShares` to FastAPI. Never place an operator-wide
access token behind anonymous public routes. G1 remains blocked until those
external requirements and real integration evidence exist.

Transport implementation references: [HTTPX custom transports](https://www.python-httpx.org/advanced/transports/)
and [HTTPCore SNI extension](https://www.encode.io/httpcore/extensions/).
