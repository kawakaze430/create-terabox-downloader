# Instructions for All Developers and Codex Agents

**Latest owner update — 2026-11-17:** Build our source-independent download engine first. Official partner approval is not a prerequisite for generic transfer work against controlled permitted sources. Keep source access separate and preserve all existing security controls. During the suspected-compromise review, keep recovery checkpoints on a named branch until the owner has verified account access. Never force-push. See the [incident review](docs/security/incident-review.md). Keep [docs/CODEX_CONTINUITY.md](docs/CODEX_CONTINUITY.md) current so another workspace can resume. The current remote is authoritative; historical documents refer to an earlier repository owner.

**NEW SESSION CONTINUITY:** First read [docs/START_HERE_PROJECT_HANDOFF.md](docs/START_HERE_PROJECT_HANDOFF.md) and [docs/PROJECT_CONVERSATION_ARCHIVE.md](docs/PROJECT_CONVERSATION_ARCHIVE.md), plus [original master prompt](docs/MASTER_DEVELOPMENT_PROMPT_2026-11-15.md). The handoff is a snapshot; always verify latest HEAD, CI, issue #2 and source before changes.

The current [repository structure](PROJECT_STRUCTURE.md), [documentation index](docs/README.md), and [recovery reports](docs/history/repository-reviews/README.md) explain file ownership and historical material. These current records supplement the dated handoff.

**Project:** Independently operated, commercially competitive TeraBox downloader website + browser extension.  
**Updated:** 2026-11-14.

## READ FIRST — canonical product intent

Do not assume the goal is a simple link downloader or a clone of one GitHub repository. The business goal is to build a **market-leading, reliable, secure, independently branded** TeraBox download and preview platform, with one shared backend and multiple clients, using suitable open-source building blocks where licensing allows.

Before changing code, read in order:
1. [README.md](README.md)
2. [docs/PRODUCT_REQUIREMENTS.md](docs/PRODUCT_REQUIREMENTS.md) — full mission, feature matrix and constraints.
3. [docs/ARCHITECTURE.md](docs/ARCHITECTURE.md) — proposed component boundaries and security.
4. [docs/ROADMAP_AND_QA.md](docs/ROADMAP_AND_QA.md) — milestones, evidence and credit-saving rules.
5. [docs/RESEARCH_AND_LICENSES.md](docs/RESEARCH_AND_LICENSES.md) — reference repos, competitor analysis, license review.

These documents describe **planned targets**, not proof of implementation. The actual code and tested behavior are the source of truth for progress. The repository was initially just a README; check current tree and commits before assuming anything works.

## Execution rules

- **Do not restart an existing implementation or overwrite working code without evidence.** Inspect current files, branches, tests, issues and outstanding PRs first.
- First assess lawful and technical feasibility of TeraBox access. Favor permitted, documented integration. Do not bypass authentication, CAPTCHA, provider access controls, premium limits, DRM, or others' rights.
- **P0:** source-independent bounded streaming, retry/recovery, integrity, cancellation and controlled local transfer tests, plus safe source admission. Continue independent engine engineering while TeraBox access is unverified. Do not claim local fixtures prove TeraBox compatibility; do not expand into unrelated premium features.
- **P1:** usable full web app, player, folders/batch only as supported, Chrome/Edge MV3 extension, CI, deployability and monitoring.
- **P2/P3:** differentiation, accounts, subscription plans and extra platforms only after proven reliability; preserve extension points without premature implementation.
- Use one coherent monorepo and **one backend API contract**, not five copied frameworks. Integrate selective code only after source audit and license verification; preserve required notices.
- Prioritize stable, well-maintained libraries for media/player, testing, observability. Never add unnecessary dependencies. Audit copyleft before incorporating into proprietary components.
- Never fabricate filename, preview, transfer status, resolution (480p/720p/1080p/4K), download URL or a “working” result.
- Keep secrets out of Git; no third-party public proxies or borrowed sessions as production foundations.
- Apply exact hostname allowlists, redirect and SSRF protections, rate limits, bounded batch/ZIP processing, error redaction and minimal data collection.
- Design mobile-first and accessible; avoid competitor trademarks/trade dress. Clearly disclose non-affiliation and privacy practices.

## Work protocol (cost-conscious)

For each task:
1. Inspect and summarize relevant existing code/behavior and expected feature acceptance.
2. Choose the smallest high-value solution; reuse existing code and suitable libraries.
3. Implement a bounded task with tests and clear commits. During incident review, preserve verified work on the recovery branch and confirm any permitted remote checkpoint. Keep incomplete work off main. Never force-push shared history or overwrite concurrent changes. Use the existing isolated checkout; do not create a worktree unless explicitly requested.
4. Run relevant lint/type/unit checks, then targeted integration/browser checks. A mocked pass is not a successful real TeraBox download.
5. Update feature status and any architecture decision or known limitation.
6. Report what changed, exact commands/tests executed, results, untested items, security/license implications, and next prioritized work.

**Don't spend credits recreating a whole system just to get more features.** If an external API stops working, first determine whether a compliant replacement exists; if not, report the blocker.

## Important references

Main inspiration: https://github.com/gitmarcus07/Teraplayer  
Additional research: https://github.com/Itz-Ashlynn/Terabox-Web , https://github.com/saahiyo/terabox-gateway , https://github.com/saahiyo/tera-peek , https://github.com/SH20RAJ/terabox-player-chrome-extension .  
Each repo's present license and source must be audited before copying. See research doc for more options.

## Definition of done

A feature is only “working” when it has meaningful, reproducible evidence: code, passing relevant automated tests and, for provider-dependent capabilities, **authorized live integration evidence**. Deployment and store publishing additionally require the owner's accounts/permissions and user-facing privacy/support notices.

The project is a **target for a market-leading product, not a claim of existing leadership**. Anyone joining should understand the entire direction from these checked-in docs, without needing a past chat.
