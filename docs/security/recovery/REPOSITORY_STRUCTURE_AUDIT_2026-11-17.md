# Repository structure audit — 17 November 2026 (India time)

The active `main` was compared with the last known project checkpoint (`35eb415`). Before this restructuring it was clean, and `origin/main` pointed to the same commit. The 62 tracked files formed the documented monorepo. The visible history did not show an unexplained replacement of application source. This is a repository-tree finding; it cannot verify GitHub account access, collaborators, tokens or earlier activity outside the visible branch. GitHub's issue/Actions API was unavailable to this environment (`Forbidden`).

## Kept running structure

| Path | Contents and role | Decision |
| --- | --- | --- |
| `services/api/app/` | FastAPI routes, validation, limits, provider contract, protected operator candidate | Keep paths and imports. Public provider still disabled until live authorization and transfer evidence. |
| `services/api/tests/`, `requirements.lock` | Offline API checks and pinned Python dependencies | Keep together with the API. |
| `apps/web/` | Next.js/TypeScript site, browser tests and npm lockfile | Keep as the website. |
| `apps/extension/` | Manifest V3 development extension and parser tests | Keep as the browser client. |
| `.github/workflows/ci.yml` | Existing API, web and extension checks | Keep CI working against the same paths. |
| `docs/` | Requirements, architecture, handoff, operator guides, research and implementation history | Keep references and the document-archive verification path. |
| `scripts/` | Reproducible, checksum-checked reference extraction | Point at the preserved archives below. |
| Repository root | README, AGENTS, 49-source study list and ignore rules | Keep stable entrypoints; the study list is referenced by existing docs. The earlier idea now lives in `AnalyseFuture/future-ideas/`. |

## Files moved for analysis, not deleted

The two uploaded third-party ZIPs were the only root files outside the active application and its project documentation. Both were moved to `AnalyseFuture/archives/`. Both needed a security exception: TeraPlayer's `cloudflare-worker/.dev.vars` contained a populated session cookie, its captured `cloudflare-worker/terabox-live.html` contained a page token, and gateway's `.env.example` contained a populated cookie setting. The current ZIPs retain those files with empty placeholders. Every other archive member remains present. The generated extraction is under `AnalyseFuture/extracted/` and is ignored; the archive script recreates it in a fresh checkout.

The original cookie-bearing ZIPs are still reachable in earlier Git history. Moving or sanitizing the current files does not erase that history. The account owner should revoke the affected sessions and review GitHub account security through GitHub's own settings. No credential value was copied into this audit.

## Project status and next boundary

The preserved [project idea TXT](../../../research/future-ideas/PROJECT_IDEA_AND_FUTURE_VISION.txt) contains the requested present capabilities, video-format ambition, limits, AI-era ideas and one/two-year future path. This restructuring does not claim a working TeraBox downloader: the public provider remains unconfigured, and authorized live metadata and a completed file transfer have not been verified. Any integration of reference ZIP code needs a separate source/license/security review and evidence of a permitted provider path.

The aim of this layout is clear ownership: `apps/` and `services/` are the running product; `docs/` describes it; `AnalyseFuture/` preserves external material and future ideas for later decisions.
