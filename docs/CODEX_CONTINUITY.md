# Codex continuation record

Updated 17 November 2026 (Asia/Kolkata). Latest owner priorities supersede the earlier PR-only/provider-first workflow: build a generic source-independent download engine, verify controlled transfers, and push each completed task directly to main when permitted. Never force-push; use a durable remote branch if protection blocks main.

## Checkpoint state

- Repository: `sarfiaroui-oss/create-terabox-downloader`; branch: `main`.
- Last confirmed remote before this record: `bf1eea238616c5bfccfc8647bc7b3931ab0914ad` (benchmark); engine `0a8117a`, extension `f36a72b` and audit `a03a4c3` also confirmed.
- The commit containing this record is itself a checkpoint; resolve its SHA with `git log -1 --format=%H -- docs/CODEX_CONTINUITY.md` and confirm against `git ls-remote origin refs/heads/main`. A file cannot contain its own final Git commit hash.
- Completed: E01 baseline source/file audit; current owner workflow reconciled. E04 configurable extension destination, deterministic six-file packaging, popup failures/tests and current website source link. No framework moves/deletions required.
- Completed E02/E03: source-independent streaming-to-file, bounded retries/backoff/Retry-After, size/SHA-256 checks, cancellation/temp cleanup, atomic no-clobber publication and strong-ETag in-call Range recovery; operator CLI. 74 engine + 3 CLI tests passed; total API suite 250 passed and pip check passed. No live TeraBox verification or new dependency.
- Controlled benchmark complete: 4 MiB, 3 repetitions/scenario, interruption after 512 KiB; clean/restart/resume verified. Resume saved 524,288 body bytes against restart, without measured speed advantage. Raw samples in docs/ENGINE_BENCHMARK_2026-11-17.json; rerun with `services/api/.venv/bin/python scripts/benchmark_download_engine.py --size-mib 4 --repeats 3`.
- Completed web metadata milestone: strict runtime/TypeScript contract guards, real returned file metadata/empty states, malformed-response rejection and stale-resolution clearing. No fake preview/download/progress action. Build/typecheck passed; 20 desktop/mobile browser checks passed (10 scenarios, including explicitly simulated metadata/error cases).
- Next: current inventory/status updates, final documentation checks and durable checkpoint. Parallel/adaptive algorithms and cross-process resume remain unimplemented.
- Working files: `services/api/app/download_engine.py`, `services/api/tests/test_download_engine.py`; client work stays under extension/packaging docs and website source link.
- Baseline: 82 tracked files, 18 tracked directories, no initial local changes, remote main at the SHA above. Fresh baseline: 173 API tests passed (one existing Starlette/httpx deprecation warning); pip check passed. Engine/client changes were not part of that baseline.
- External limitations: current-fork GitHub PR/CI API previously returned Forbidden; native Git read/push works. TeraBox access unverified; generic engine work does not depend on partner credentials. Known historical ZIP sessions require owner revocation; no values are exposed here.
- E04 validation: 50 extension/parser/popup/package tests passed, popup syntax passed; default package command passed. Manifest remains MV3 activeTab-only. Installed Chrome/Edge and store submission unrun. Website source href only changed; full web checks follow in E05.

## Current queue

1. E01: audited architecture and persistent checkpoint (this record).
2. E02: bounded single-stream transfer, retry, independent hash/size, atomic completion, cancellation cleanup; actual local socket tests.
3. E03: validator-safe in-call Range recovery only after E02; strict range/size/version validation; benchmark controlled fixtures before any speed claim.
4. E04: extension destination validation, deterministic packaging, install guide, current source link.
5. E05: full affected API/client/browser checks, current inventories/status and durable final checkpoint.

## Resume commands

```bash
git status --short
git fetch origin
git log -5 --oneline
git ls-remote origin refs/heads/main
PYTHONPATH=services/api services/api/.venv/bin/python -m pytest -q services/api/tests
services/api/.venv/bin/python -m pip check
node --test apps/extension/tests/*.test.mjs
# apps/web: NEXT_TELEMETRY_DISABLED=1 npm run build && npm run typecheck
```

Use the existing checkout, no worktree. Preserve unrelated changes. Stage named files only. Keep incomplete code off main. Source-independent tests prove transfer behavior for those fixtures, not live TeraBox downloads. Next session should inspect the current record and engine design before repeating work.
