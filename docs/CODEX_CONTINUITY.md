# Codex continuation record

Updated 18 November 2026 (Asia/Kolkata). Work is on `recovery/incident-review-2026-11-18` while the owner verifies GitHub account and repository access. Keep `main` at the reviewed baseline and use normal, non-force pushes for recovery checkpoints.

## Recovery checkpoints

- GitHub `main` was `c0163c24ffdcf4391c0e2874cb508f52172958f1`. The named recovery branch contains `1cd4c80410a40ddc427a6f8005564c4235672dd3`, the incident review and all 21 former `AnalyseFuture/` dispositions, and `bb37749a8a73a365c27465032c041f867f07ed4f`, the first recovery continuity update.
- The commit that last updated this record adds the controlled browser-to-engine transfer fixture and its CI checks. Find the SHA with `git log -1 --format=%H -- docs/CODEX_CONTINUITY.md` and compare it to `git ls-remote origin refs/heads/recovery/incident-review-2026-11-18`.
- Current evidence includes the [incident review and owner actions](security/incident-review.md), [97-file inventory](history/repository-reviews/baseline-inventory-2026-11-18.md), [21-path move ledger](history/repository-reviews/move-ledger-2026-11-18.md), and [baseline checks](history/repository-reviews/baseline-validation-2026-11-18.md). The local bundle contains sensitive historical archives. Keep it private.
- The baseline passed 250 API, 50 extension, and 20 Playwright tests, web build/typecheck, dependency consistency and advisory checks, Word/archive verification and nine bounded engine benchmark samples. The relocated archives passed extraction and repeat verification in a disposable directory. Relative Markdown links and the Word validator passed after migration.
- The opt-in [fixture procedure](LOCAL_DEVELOPMENT.md#local-browser-to-engine-transfer-fixture) exercises progress, cancellation, completion, and file delivery with a fixed source and expiring job capabilities. The updated [engine guide](DOWNLOAD_ENGINE.md) describes the transfer boundary. The [API fixture](../services/api/app/fixture_transfers.py), [website component](../apps/web/app/fixture-transfer.tsx), and [browser checks](../apps/web/tests/fixture-transfer.spec.ts) are the milestone files.
- Post-migration verification passed 262 API tests, including 12 fixture checks, plus 50 extension tests, 20 default browser tests, four fixture browser tests, both web builds and TypeScript checks. The independent 4 MiB engine benchmark also completed nine verified transfers. There were no failures or skips in these suites. The Python Starlette/httpx deprecation and Node color warnings remain.
- TeraBox OAuth, actual TeraBox file delivery, production ingress testing, public deployment, and remote CI results remain unverified. Installed browser extension activation was blocked by the cloud Chromium policy.

## Resume

Use the existing checkout. Recheck GitHub and branch state before edits. Preserve unrelated changes and stage only the completed milestone.

```bash
git status --short
git ls-remote origin refs/heads/main refs/heads/recovery/incident-review-2026-11-18
git fetch origin refs/heads/recovery/incident-review-2026-11-18
# In a fresh checkout, create the local recovery branch from the fetched checkpoint:
git switch -c recovery/incident-review-2026-11-18 FETCH_HEAD

PYTHONPATH=services/api services/api/.venv/bin/python -m pytest -q services/api/tests
node --test apps/extension/tests/*.test.mjs
```

Run [ordinary web checks](LOCAL_DEVELOPMENT.md#repeatable-browser-checks) and the [opt-in browser suite](LOCAL_DEVELOPMENT.md#local-browser-to-engine-transfer-fixture) on fresh local services. The default site and API leave the fixture disabled. The fixture has separate CI coverage with the existing workflow permissions.

## Next five tasks

| Priority | Files | Goal, prerequisites and acceptance |
| --- | --- | --- |
| 1 | `services/api/app/provider.py`, `egress.py`, fixture tests | Design an operator-owned source adapter after confirming one controlled source and its authorization. Test exact-host policy, authorization expiry, wrong actor and arbitrary-input rejection. Advance when a real owned HTTPS source delivers its independently verified bytes. |
| 2 | `services/api/app/fixture_transfers.py`, `limits.py`, focused API tests | Design production session ownership and job storage after deciding whether the service will run multiple workers. Exercise concurrent start/cancel/delivery, quota fairness, race-free cleanup and restart recovery before enabling broader use. |
| 3 | `services/api/app/download_engine.py`, `services/api/tests/test_download_engine.py`, `scripts/benchmark_download_engine.py` | Measure aggregate bytes and retry cost under controlled latency and interruptions. Test a total retry-byte budget and consistent progress before adding parallel scheduling. |
| 4 | `apps/web/app/api-contract.ts`, `page.tsx`, `apps/web/tests/` | Connect an authorized adapter to the existing typed website once session ownership is available. Verify keyboard and mobile start/cancel, expiry, integrity failure and completed file delivery. |
| 5 | `apps/extension/`, `docs/EXTENSION_DEVELOPMENT.md`, `docs/OPERATOR_VALIDATION.md` | Run the packaged extension in owner-approved Chrome and Edge with an owned site origin. Verify its active-tab permission and fragment handoff. Record permitted live-source evidence separately when an authorized account and source are available. |

The immediate handoff is priority 1 on the recovery branch. The owner can investigate GitHub access and revoke potentially exposed sessions independently of generic engine work.
