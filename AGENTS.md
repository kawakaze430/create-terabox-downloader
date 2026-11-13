# Instructions for All Developers and Codex Agents

**Project:** Independently operated, commercially competitive TeraBox downloader website + browser extension.  
**Updated:** 2026-11-13.

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
- **P0:** link validation, authorized metadata and download, error handling, SSRF protection and repeatable live tests. If P0 is blocked, report blocker and do not spend credits on unrelated premium features.
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
3. Implement a bounded change, with tests; prefer PRs and clear commits.
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
