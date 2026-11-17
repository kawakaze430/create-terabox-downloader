# Repository organization audit — 17 November 2026

Baseline: `076205b8243ce621e7251865d44d645e160fc515`, current repository `sarfiaroui-oss/create-terabox-downloader`. 82 tracked files in 18 non-root tracked directories. Initial working tree was clean; native Git confirmed remote main. This is source/document inspection, not live TeraBox evidence.

## Findings and safe actions

- Keep conventional FastAPI, Next.js and MV3 layouts. Their language boundaries communicate through the existing internal API; no framework move/rewrite helps byte transfer.
- Existing URL parsers are separate trust/language boundaries, not blindly removable duplicates. Test equivalence with shared safe cases when extending formats.
- Official operator probe has a small memory-free checksum loop but is source-specific and capped at 10 MiB. Keep it stable; implement a generic streaming-to-disk engine alongside it, rather than weakening source policy.
- Earlier PR-only, main-only, and provider-first instructions conflict. AGENTS and the status entry now explicitly prioritize the newest engine prompt; preserve dated historical text.
- Website source href still points to the old owner; repair it as an isolated client change. Extension destination needs validated configurable release settings instead of hardcoded localhost.
- Full reference ZIPs remain isolated; their 341 nested entries are inventoried in AnalyseFuture/archives/ZIP_MEMBER_INVENTORY.txt. No worker, cron, helper agent or borrowed-session path is part of startup.
- Unique recovery reports and verbatim old prompts remain at stable paths. No confirmed redundant source file was found that warrants deletion; broad similar planning documents have distinct dated provenance.
- Versioned dependency locks remain untouched. No dependency is removed solely because a text search misses a dynamic/framework use. No new engine dependency is needed.
- Known historical session exposure remains an owner revocation action; current ZIP sanitization does not erase old blobs. No secret values are included here.
- Generated .venv, node_modules, .next, test caches and extracted references remain ignored. No stale active import was identified in the source review; tests/builds provide the execution check.
- No application source is moved, archived or consolidated in this milestone. New files have real engine/test/continuation responsibilities and will be mapped in the current status guide.

## Complete baseline classification

Each baseline tracked path is assigned a responsibility. Detailed per-file behavior is in PROJECT_STATUS_AND_TASKS.md; this table establishes coverage and disposition. All baseline paths are retained.

| Path | Responsibility | Disposition |
| --- | --- | --- |
| `.github/workflows/ci.yml` | Automation configuration | Retain |
| `.gitignore` | Generated output/secrets exclusion configuration | Retain |
| `AGENTS.md` | Current documentation/instructions | Retain |
| `AnalyseFuture/ARCHIVED_FILES_MANIFEST.txt` | Research/recovery/history; preserve | Retain |
| `AnalyseFuture/COMPLETE_FILE_INVENTORY.txt` | Research/recovery/history; preserve | Retain |
| `AnalyseFuture/CONSOLIDATION_REPORT.txt` | Research/recovery/history; preserve | Retain |
| `AnalyseFuture/DUPLICATE_ANALYSIS.txt` | Research/recovery/history; preserve | Retain |
| `AnalyseFuture/FEATURE_INVENTORY.txt` | Research/recovery/history; preserve | Retain |
| `AnalyseFuture/MIGRATION_SUMMARY.txt` | Research/recovery/history; preserve | Retain |
| `AnalyseFuture/NEXT_DEVELOPER_INSTRUCTIONS.txt` | Research/recovery/history; preserve | Retain |
| `AnalyseFuture/ORIGINAL_TO_NEW_PATH_MAPPING.txt` | Research/recovery/history; preserve | Retain |
| `AnalyseFuture/PROJECT_VISION_AND_FUTURE_ROADMAP.txt` | Research/recovery/history; preserve | Retain |
| `AnalyseFuture/README.md` | Research/recovery/history; preserve | Retain |
| `AnalyseFuture/REPOSITORY_AUDIT.txt` | Research/recovery/history; preserve | Retain |
| `AnalyseFuture/SECURITY_AUDIT.txt` | Research/recovery/history; preserve | Retain |
| `AnalyseFuture/TECHNICAL_DEBT.txt` | Research/recovery/history; preserve | Retain |
| `AnalyseFuture/TEST_AND_VALIDATION_REPORT.txt` | Research/recovery/history; preserve | Retain |
| `AnalyseFuture/WORK_PROGRESS.txt` | Research/recovery/history; preserve | Retain |
| `AnalyseFuture/archives/REFERENCE_ARCHIVES.md` | Research/recovery/history; preserve | Retain |
| `AnalyseFuture/archives/Teraplayer-main.zip` | Archived third-party source; not executed | Retain |
| `AnalyseFuture/archives/ZIP_MEMBER_INVENTORY.txt` | Research/recovery/history; preserve | Retain |
| `AnalyseFuture/archives/terabox-gateway-main.zip` | Archived third-party source; not executed | Retain |
| `AnalyseFuture/future-ideas/PROJECT_IDEA_AND_FUTURE_VISION.txt` | Research/recovery/history; preserve | Retain |
| `AnalyseFuture/recovery-notes/REPOSITORY_STRUCTURE_AUDIT_2026-11-17.md` | Research/recovery/history; preserve | Retain |
| `PROJECT_STATUS_AND_TASKS.md` | Current documentation/instructions | Retain |
| `PROJECT_STRUCTURE.md` | Current documentation/instructions | Retain |
| `PUBLIC_REPOSITORY_STUDY_LIST.txt` | Research index | Retain |
| `README.md` | Current documentation/instructions | Retain |
| `apps/extension/links.mjs` | Extension source/configuration | Retain |
| `apps/extension/manifest.json` | Extension source/configuration | Retain |
| `apps/extension/popup.css` | Extension source/configuration | Retain |
| `apps/extension/popup.html` | Extension source/configuration | Retain |
| `apps/extension/popup.js` | Extension source/configuration | Retain |
| `apps/extension/tests/links.test.mjs` | Extension tests | Retain |
| `apps/web/.env.example` | Website configuration/dependencies | Retain |
| `apps/web/app/globals.css` | Website source | Retain |
| `apps/web/app/layout.tsx` | Website source | Retain |
| `apps/web/app/page.tsx` | Website source | Retain |
| `apps/web/next-env.d.ts` | Website configuration/dependencies | Retain |
| `apps/web/next.config.ts` | Website configuration/dependencies | Retain |
| `apps/web/package-lock.json` | Website configuration/dependencies | Retain |
| `apps/web/package.json` | Website configuration/dependencies | Retain |
| `apps/web/playwright.config.ts` | Website configuration/dependencies | Retain |
| `apps/web/tests/core.spec.ts` | Website tests | Retain |
| `apps/web/tsconfig.json` | Website configuration/dependencies | Retain |
| `docs/ARCHITECTURE.md` | Current documentation/instructions | Retain |
| `docs/IMPLEMENTATION_CHECKLIST.md` | Current documentation/instructions | Retain |
| `docs/IMPLEMENTATION_LOG.md` | Current documentation/instructions | Retain |
| `docs/LOCAL_DEVELOPMENT.md` | Current documentation/instructions | Retain |
| `docs/MASTER_DEVELOPMENT_PROMPT_2026-11-15.md` | Historical continuity; preserve | Retain |
| `docs/OFFICIAL_OPEN_PLATFORM.md` | Current documentation/instructions | Retain |
| `docs/OPERATOR_VALIDATION.md` | Current documentation/instructions | Retain |
| `docs/PRODUCT_REQUIREMENTS.md` | Current documentation/instructions | Retain |
| `docs/PROJECT_CONVERSATION_ARCHIVE.md` | Historical continuity; preserve | Retain |
| `docs/PROJECT_MASTER_HANDOFF.docx` | Historical continuity; preserve | Retain |
| `docs/PROJECT_SOURCE_INDEX_2026-11-16.md` | Historical continuity; preserve | Retain |
| `docs/PROVIDER_FEASIBILITY.md` | Current documentation/instructions | Retain |
| `docs/README.md` | Current documentation/instructions | Retain |
| `docs/RESEARCH_AND_LICENSES.md` | Current documentation/instructions | Retain |
| `docs/ROADMAP_AND_QA.md` | Current documentation/instructions | Retain |
| `docs/START_HERE_PROJECT_HANDOFF.md` | Current documentation/instructions | Retain |
| `docs/verify_handoff_archive.py` | Development verification utility | Retain |
| `scripts/unpack_reference_archives.py` | Development verification utility | Retain |
| `services/api/.env.example` | Backend dependency/configuration | Retain |
| `services/api/app/__init__.py` | Backend; provider/access/security (engine added separately) | Retain |
| `services/api/app/egress.py` | Backend; provider/access/security (engine added separately) | Retain |
| `services/api/app/limits.py` | Backend; provider/access/security (engine added separately) | Retain |
| `services/api/app/links.py` | Backend; provider/access/security (engine added separately) | Retain |
| `services/api/app/main.py` | Backend; provider/access/security (engine added separately) | Retain |
| `services/api/app/models.py` | Backend; provider/access/security (engine added separately) | Retain |
| `services/api/app/official_shares.py` | Backend; provider/access/security (engine added separately) | Retain |
| `services/api/app/open_platform.py` | Backend; provider/access/security (engine added separately) | Retain |
| `services/api/app/preflight.py` | Backend; provider/access/security (engine added separately) | Retain |
| `services/api/app/provider.py` | Backend; provider/access/security (engine added separately) | Retain |
| `services/api/requirements.lock` | Backend dependency/configuration | Retain |
| `services/api/requirements.txt` | Backend dependency/configuration | Retain |
| `services/api/tests/test_api.py` | Backend tests | Retain |
| `services/api/tests/test_egress.py` | Backend tests | Retain |
| `services/api/tests/test_limits.py` | Backend tests | Retain |
| `services/api/tests/test_official_shares.py` | Backend tests | Retain |
| `services/api/tests/test_open_platform.py` | Backend tests | Retain |
| `services/api/tests/test_provider_contract.py` | Backend tests | Retain |

## Directories

- `.github`
- `.github/workflows`
- `AnalyseFuture`
- `AnalyseFuture/archives`
- `AnalyseFuture/future-ideas`
- `AnalyseFuture/recovery-notes`
- `apps`
- `apps/extension`
- `apps/extension/tests`
- `apps/web`
- `apps/web/app`
- `apps/web/tests`
- `docs`
- `scripts`
- `services`
- `services/api`
- `services/api/app`
- `services/api/tests`

New checkpoint docs: `docs/CODEX_CONTINUITY.md`, `docs/DOWNLOAD_ENGINE.md`, and this audit. Future engine/client additions must update the current guide rather than modifying this dated baseline inventory.
