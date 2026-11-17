# Project structure

This repository is one TeraBox-oriented media product with a Python API, a TypeScript website, and a small browser extension. The running code keeps each framework's normal layout. Research projects, older ideas, and recovery records are separate from the application under `AnalyseFuture/`. No AI media feature or live TeraBox downloader is currently enabled.

The source-independent transfer engine is now implemented within the Python service, separately from source authorization. See [engine design/results](docs/DOWNLOAD_ENGINE.md) and [current continuation](docs/CODEX_CONTINUITY.md). Local HTTP fixture tests prove generic streaming/recovery, not TeraBox access. The [new organization audit](docs/REPOSITORY_ORGANIZATION_AUDIT.md) classified all 82 baseline files and 18 directories; unique historical records and conventional framework paths were retained.

```text
create-terabox-downloader/
├── README.md                         project entry point and current status
├── AGENTS.md                         development rules and continuity
├── PROJECT_STRUCTURE.md              this ownership map
├── PROJECT_STATUS_AND_TASKS.md       complete current file/task/feature handoff
├── PUBLIC_REPOSITORY_STUDY_LIST.txt   stable 49-source research index
├── .github/workflows/ci.yml          checks for the three active surfaces
├── apps/
│   ├── web/                          Next.js website, config, tests, lockfile
│   └── extension/                    Manifest V3 popup, link parser, tests
├── services/api/                     FastAPI app, tests, locked dependencies
├── scripts/                          extraction, extension packaging, engine benchmark
├── docs/                             product, architecture, setup, provider,
│                                     research, and continuity documents
└── AnalyseFuture/
    ├── archives/                     isolated third-party ZIPs and guide
    ├── future-ideas/                 preserved earlier project idea
    ├── recovery-notes/               dated previous structure audit
    ├── PROJECT_VISION_AND_FUTURE_ROADMAP.txt
    └── *.txt                          current recovery inventories and reports
```

## Where a feature belongs

| Responsibility | Current files | Relationship |
| --- | --- | --- |
| Independent byte transfer | `services/api/app/download_engine.py`, `download_cli.py`, corresponding local-socket/CLI tests | Already-approved source → bounded stream/retry/resume/integrity → private temp → atomic completion; no OAuth dependency or public arbitrary-URL endpoint |
| Share-link admission | `services/api/app/links.py`, `apps/extension/links.mjs` | The API is authoritative. The extension performs local preflight before opening the site. Both have their own tests because they run in different languages and trust boundaries. |
| Public API and contract | `services/api/app/main.py`, `models.py`, `provider.py` | The website calls the versioned API. The default provider is intentionally unconfigured. |
| API privacy and request limits | `services/api/app/limits.py` and API routes | Bounds requests and sanitizes public errors. |
| Candidate upstream access | `services/api/app/open_platform.py`, `official_shares.py`, `egress.py`, `preflight.py` | Operator-only, offline-tested integration candidate. It is separate from anonymous public routes until real authorization and file-transfer proof exist. |
| Website | `apps/web/app/`, `apps/web/next.config.ts`, `apps/web/tests/` | Next.js page, styling, security headers and browser checks. Its npm manifest and lockfile stay with the app. |
| Internal client validation | `apps/web/app/api-contract.ts` | Runtime response guards and small TypeScript metadata contracts, not a public SDK or generated package |
| Browser extension | `apps/extension/manifest.json`, popup files, `links.mjs`, `tests/` | Minimal-permission browser handoff to the website. |
| Extension release config | `apps/extension/config.mjs`, `scripts/package_extension.py`, `docs/EXTENSION_DEVELOPMENT.md` | Validated local/owned HTTPS origin; deterministic minimal ZIP without changing source config/permissions |
| Controlled engine measurements | `scripts/benchmark_download_engine.py`, `docs/ENGINE_BENCHMARK_2026-11-17.json` | Reproducible local restart/resume body-byte measurements; no parallel/TeraBox speed claim |
| Reproducible dependencies | `services/api/requirements.lock`, `apps/web/package-lock.json` | Pinned installs remain next to their consumers. |
| CI and developer entrypoints | `.github/workflows/ci.yml`, `docs/LOCAL_DEVELOPMENT.md`, `AGENTS.md` | Existing command paths remain stable. |
| Product and research records | `docs/`, `PUBLIC_REPOSITORY_STUDY_LIST.txt` | Historical and current documents remain available; the root study list is a widely referenced public entrypoint. |
| External source references | `AnalyseFuture/archives/`, `scripts/unpack_reference_archives.py` | ZIPs are preserved but excluded from imports, builds and CI. Generated extraction lives in ignored `AnalyseFuture/extracted/`. |

The complete path-by-path classification is in [COMPLETE_FILE_INVENTORY.txt](AnalyseFuture/COMPLETE_FILE_INVENTORY.txt), and the feature-level classification is in [FEATURE_INVENTORY.txt](AnalyseFuture/FEATURE_INVENTORY.txt). [ORIGINAL_TO_NEW_PATH_MAPPING.txt](AnalyseFuture/ORIGINAL_TO_NEW_PATH_MAPPING.txt) records each move. The design deliberately leaves the small active Python and Next.js modules in their conventional framework locations: a new `features/` or `shared/` tree would add imports and build paths without consolidating a real duplicate implementation.

## Documentation and historical material

`docs/` is the current documentation collection. Its [documentation index](docs/README.md) groups requirements, architecture, roadmap, local setup, provider validation, research, and handoff files by purpose. These files have many stable cross-links, so filenames are kept for compatibility. `docs/verify_handoff_archive.py` remains beside the handoff document because CI calls it there. The immutable source index and verbatim original prompt retain historical paths as evidence.

`AnalyseFuture/` is a review area, never an application entrypoint. The two uploaded ZIPs remain whole except for credential-like values emptied in the current copies; earlier Git history still holds the original blobs. The earlier project idea is preserved in `future-ideas/`; the current vision is the roadmap at the `AnalyseFuture/` root. The dated earlier structure audit is under `recovery-notes/`. None of these files should be imported, executed, installed or deployed as application code without a separate review.

## Generated and ignored local folders

`services/api/.venv/`, Python `__pycache__/`, `.pytest_cache/`, `apps/web/node_modules/`, `.next/`, `test-results/`, `*.tsbuildinfo`, and `AnalyseFuture/extracted/` are local generated outputs. They are classified as build, environment, test, or extracted-reference state and are not tracked source. The ZIPs plus `scripts/unpack_reference_archives.py` reproduce the extracted source; [ZIP_MEMBER_INVENTORY.txt](AnalyseFuture/archives/ZIP_MEMBER_INVENTORY.txt) names all 341 nested archive entries. No generated file is needed to understand or restore the repository structure.

## Rules for future additions

Put new API routes, provider logic and their Python tests under `services/api/`; web components and browser tests under `apps/web/`; extension behavior and tests under `apps/extension/`. Add shared schemas only when at least two active consumers need the same generated contract. Keep documentation in `docs/` and preservation/recovery material in `AnalyseFuture/`. Record a moved path in the mapping report and repair references before committing. Never treat ZIP code as a second running app or claim that a valid-looking link proves a completed TeraBox transfer.

The owner first requested documentation-only restructuring, then authorized a follow-up validation pass. The API, extension, browser, build, type, archive and dependency checks passed locally; see [TEST_AND_VALIDATION_REPORT.txt](AnalyseFuture/TEST_AND_VALIDATION_REPORT.txt) for the exact evidence and live-provider limits.
