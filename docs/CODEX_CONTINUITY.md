# Codex continuation record

Updated 18 November 2026 (Asia/Kolkata). Resume current work from the recovery branch while the owner verifies GitHub account and repository access. Keep main at the owner's reviewed baseline and never force-push.

## Current recovery checkpoint

- Work branch: `recovery/incident-review-2026-11-18`. Verified GitHub checkpoint `1cd4c80410a40ddc427a6f8005564c4235672dd3` preserves the evidence record and reorganizes all 21 former `AnalyseFuture/` paths.
- GitHub `main` at review time: `c0163c24ffdcf4391c0e2874cb508f52172958f1`. Recheck both refs with `git ls-remote origin refs/heads/main refs/heads/recovery/incident-review-2026-11-18`. Use the existing isolated checkout and preserve unrelated changes.
- Current records: [incident evidence and owner actions](security/incident-review.md), [97-file baseline inventory](history/repository-reviews/baseline-inventory-2026-11-18.md), [migration ledger](history/repository-reviews/move-ledger-2026-11-18.md), and [baseline verification](history/repository-reviews/baseline-validation-2026-11-18.md).
- Fresh baseline passed 250 API, 50 extension, and 20 Playwright tests, web build/typecheck, package advisories, Word/archive validation and nine bounded local engine samples. After migration, the links and Word verifier passed, and both relocated archives restored and reverified in a disposable directory. Browser-based extension installation is blocked by the cloud Chromium policy.
- Next action: finish and verify the opt-in, loopback-only controlled fixture job flow. The public TeraBox provider remains disabled and the owner needs to review account settings and revoke affected historical sessions.

## Earlier engine and client checkpoint state

- Repository: `sarfiaroui-oss/create-terabox-downloader`; branch: `main`.
- Last confirmed remote before this record: `5b9ac5709f22e9409c3b51d680b681855a660aff` (typed website); benchmark `bf1eea2`, engine `0a8117a`, extension `f36a72b` and audit `a03a4c3` also confirmed on main.
- The commit containing this record is itself a checkpoint; resolve its SHA with `git log -1 --format=%H -- docs/CODEX_CONTINUITY.md` and confirm against `git ls-remote origin refs/heads/main`. A file cannot contain its own final Git commit hash.
- Completed: E01 baseline source/file audit; current owner workflow reconciled. E04 configurable extension destination, deterministic six-file packaging, popup failures/tests and current website source link. No framework moves/deletions required.
- Completed E02/E03: source-independent streaming-to-file, bounded retries/backoff/Retry-After, size/SHA-256 checks, cancellation/temp cleanup, atomic no-clobber publication and strong-ETag in-call Range recovery; operator CLI. 74 engine + 3 CLI tests passed; total API suite 250 passed and pip check passed. No live TeraBox verification or new dependency.
- Controlled benchmark complete: 4 MiB, 3 repetitions/scenario, interruption after 512 KiB; clean/restart/resume verified. Resume saved 524,288 body bytes against restart, without measured speed advantage. Raw samples in docs/ENGINE_BENCHMARK_2026-11-17.json; rerun with `services/api/.venv/bin/python scripts/benchmark_download_engine.py --size-mib 4 --repeats 3`.
- Completed web metadata milestone: strict runtime/TypeScript contract guards, real returned file metadata/empty states, malformed-response rejection and stale-resolution clearing. No fake preview/download/progress action. Build/typecheck passed; 20 desktop/mobile browser checks passed (10 scenarios, including explicitly simulated metadata/error cases).
- E05 complete: current file/feature/command documentation reconciled; all 97 tracked files mapped. No source moved/deleted, no dependency/lock changes. Final documentation checkpoint follows the five confirmed implementation/audit checkpoints listed above.
- No unfinished application work is part of this checkpoint. Parallel/adaptive scheduling, bandwidth shaping, cross-process resume, expiring-source refresh and browser transfer jobs remain unimplemented.
- Baseline: branch `work`, 82 tracked files/18 directories, clean at `076205b8243ce621e7251865d44d645e160fc515`; switched to main from origin. Current: main, 97 tracked files/18 directories. Fresh baseline 173 API tests became 250 after engine/CLI additions; the existing Starlette/httpx deprecation remains.
- External limitations: current-fork GitHub PR/CI API previously returned Forbidden; native Git read/push works. TeraBox access unverified; generic engine work does not depend on partner credentials. Known historical ZIP sessions require owner revocation; no values are exposed here.
- E04 validation: 50 extension/parser/popup/package tests passed, popup syntax/default package passed. Manifest remains MV3 activeTab-only. Website build/typecheck and all 20 desktop/mobile browser checks passed after typed metadata changes. Installed Chrome/Edge, production hosting and store submission remain unrun.

## Earlier implementation checkpoints

1. E01 `a03a4c3`: complete initial classification, newest owner priorities, engine architecture and continuity.
2. E04 `f36a72b`: extension destination/popup/package and current source link.
3. E02/E03 `0a8117a`: independent streaming/retry/integrity/recovery/CLI and 77 new tests.
4. Benchmark `bf1eea2`: controlled measured byte/time/allocation samples and script.
5. Website `5b9ac57`: runtime types/metadata/stale states and 20 passing browser checks.
6. Final documentation checkpoint: resolve the commit containing this record with the command above; verify main on the remote. All earlier pushes succeeded; no failed push or local-only completed application work remains.

## Next five recommended tasks

1. **Trusted source-to-job adapter:** design an operator-controlled source registry and scoped opaque file/job ownership before a visitor engine endpoint. Files: `provider.py`, `main.py`, `models.py`, `download_engine.py`, focused API tests. Never accept visitor arbitrary URLs/output paths or share an operator credential.
2. **Observable browser transfer state:** connect only that trusted job flow to `apps/web/app/api-contract.ts` and `page.tsx`, using actual engine progress/cancellation and verified completion. Add browser/API tests; keep metadata-only actions truthful until delivery exists.
3. **Bounded source recovery policy:** decide aggregate retry-byte/bandwidth budgets and adapter-controlled expiry refresh, with adversarial fixture tests in `test_download_engine.py`. Cross-process resume needs a separately reviewed identity/sidecar design; do not append untrusted partial files.
4. **Measured scheduling investigation:** extend `scripts/benchmark_download_engine.py` with controlled latency/rate/error conditions before considering bounded parallel ranges/adaptive concurrency. Require unchanged validators, complete range coverage, cancellation and final size/hash; retain simple sequential fallback.
5. **Installed client and real source evidence:** follow `docs/EXTENSION_DEVELOPMENT.md` in actual Chrome/Edge with owned HTTPS configuration; investigate a legitimate user-initiated TeraBox/direct-source workflow without bypasses. Record live source limits separately; no partnership application is needed to continue generic engine work.

## Resume commands

```bash
git status --short
git fetch origin
git log -5 --oneline
git ls-remote origin refs/heads/main
PYTHONPATH=services/api services/api/.venv/bin/python -m pytest -q services/api/tests
services/api/.venv/bin/python -m pip check
node --test apps/extension/tests/*.test.mjs
services/api/.venv/bin/python scripts/benchmark_download_engine.py --size-mib 4 --repeats 3
cd apps/web
NEXT_TELEMETRY_DISABLED=1 npm run build
npm run typecheck
PATH=/workspace/create-terabox-downloader/services/api/.venv/bin:$PATH \
PLAYWRIGHT_CHROMIUM_EXECUTABLE_PATH=/usr/bin/chromium \
NEXT_TELEMETRY_DISABLED=1 npm run test:e2e
```

Use the existing checkout, no worktree. Preserve unrelated changes. Stage named files only. Keep incomplete code off main. Source-independent tests prove transfer behavior for those fixtures, not live TeraBox downloads. Next session should inspect the current record and engine design before repeating work.

Validation commands already completed in this session: API pytest (250), pip check,
extension syntax/Node tests (50), web build/typecheck and Playwright (20), controlled
benchmark and packaging command. No fresh vulnerability audit, current-fork Actions
success, full-production load test or live TeraBox transfer is claimed. Development
servers started for browser validation were stopped by the runner; future sessions
must start required services again. Old onboarding server reuse caused stale assets
in an initial attempt; final browser results came from a fresh current build.
