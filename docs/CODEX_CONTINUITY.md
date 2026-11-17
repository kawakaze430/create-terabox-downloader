# Codex continuation record

Updated 18 November 2026 (Asia/Kolkata). Work is on `recovery/incident-review-2026-11-18` while the owner verifies GitHub account and repository access. Keep `main` at the reviewed baseline and use normal, non-force pushes for recovery checkpoints.

## Managed-download release candidate

- The extension checkpoint `25b1b01a3a0180d75f250bbe5c4b07fddd3fcdbf` adds homepage access from unsupported tabs and preserves the fragment handoff from supported shares. The engine checkpoint `4fbbec0fa6728e008096590110742cd731558277` adds cumulative retry-byte accounting and an optional hard body budget.
- This record's latest commit adds the managed API and browser catalog, a single-worker container deployment, and separate controlled and live-source acceptance commands. Find the checkpoint with `git log -1 --format=%H -- docs/CODEX_CONTINUITY.md` and verify the recovery ref with `git ls-remote`.
- Final local results were 289 API tests, 52 extension tests, 20 default browser tests, four local fixture tests, eight managed UI tests with simulated API responses, and two managed browser-to-engine tests with the real local services and a controlled upstream transport. Build/typecheck, dependency consistency, and Word archive validation passed. The independently verified body counts in the 4 MiB benchmark were 4,194,304 on resume and 4,718,715 on restart after a 524,411-byte interruption.
- Both container targets built. Local Compose verified the homepage, API health and share validation through the ingress. The managed HTTPS smoke proved sign-in, access controls, catalog listing and private storage with a locally trusted TLS certificate. Public hosting and real provider credentials were outside the smoke.
- The commit-pinned project README was retrieved through the managed HTTPS proxy and matched the Git bytes. The production pinning path failed because public direct DNS is unavailable in the task runtime, including from the API container. Run the [live-source acceptance mode](MANAGED_DOWNLOADS.md#acceptance-checks) where direct egress is available. Keep normal destination, TLS, and DNS validation in place.
- The TeraBox operator preflight remains unconfigured. The owner still needs permitted provider access and a small authorized fixture for a live check. Chromium's managed installation policy blocks the installed-extension check here. Use the [deployment guide](MANAGED_DOWNLOADS.md), [operator runbook](OPERATOR_VALIDATION.md), and [extension packaging procedure](EXTENSION_DEVELOPMENT.md) for those release steps.

## Recovery checkpoints

- GitHub `main` was `c0163c24ffdcf4391c0e2874cb508f52172958f1`. The named recovery branch contains `1cd4c80410a40ddc427a6f8005564c4235672dd3`, the incident review and all 21 former `AnalyseFuture/` dispositions, and `bb37749a8a73a365c27465032c041f867f07ed4f`, the first recovery continuity update.
- `5c0c8384879d9b827585de2ec5fdc217f5416c73` adds the controlled browser-to-engine transfer fixture and its CI checks. The inventory supplement records all eight new paths. Find the latest recovery checkpoint with `git log -1 --format=%H -- docs/CODEX_CONTINUITY.md` and compare it to `git ls-remote origin refs/heads/recovery/incident-review-2026-11-18`.
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

## Release acceptance still pending

1. Run managed live-source acceptance from a host with approved direct egress. Compare the browser-delivered file with the pinned source hash.
2. Deploy to an owned domain with the production access key and registry provisioned privately. Verify public TLS, ingress quotas, and restricted logs. Review GitHub access and the earlier session exposure before updating main.
3. Run the packaged extension in owner-approved Chrome and Edge against that domain. Confirm both homepage launch and supported-share fragment handoff.
4. Complete the authorized TeraBox operator preflight before exposing provider results to visitors. Real video, folder, batch, and preview behavior depends on the capabilities verified there.
