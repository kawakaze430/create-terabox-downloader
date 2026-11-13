# TeraBox Downloader Platform — Product Vision & Developer Hub

> **Status (2026-11-13):** Development foundation added on the `feat/phase-0-foundation` branch: FastAPI link-validation endpoints with automated tests, a Next.js development UI, a Chrome/Edge Manifest V3 popup, and GitHub CI configuration. **These are not a working TeraBox downloader**. Live file metadata, previews, and downloads remain unimplemented and unverified.

## Our mission

Build an **original, independently branded, market-leading TeraBox file preview and downloader software platform**: a high-quality responsive website, Chrome/Edge browser extensions, a shared secure backend/API, strong reliability, and a long-term path toward accounts, developer API and optional premium services.

We are **not** looking to ship a quick clone or merely combine random repositories. We want to compete with well-known TeraBox downloader products through **real functionality, user trust, performance, great UX, privacy, accessibility and sustainable operating costs**. “Market-leading” describes an aspiration, not a verified current ranking.

The product should be owned and operated through our own GitHub, hosting, infrastructure, domain, brand, secrets and release processes. We may reuse **appropriately licensed** components and ideas, but we must preserve notices, avoid unnecessary vendor dependencies and remain transparent that TeraBox itself is an upstream external service.

## Everything a new developer needs to read

| Document | Purpose |
| --- | --- |
| **[AGENTS.md](AGENTS.md)** | Starting instructions for Codex, new agents and all developers; workflow, guardrails, credit-saving priorities. |
| **[Full Product Requirements](docs/PRODUCT_REQUIREMENTS.md)** | Comprehensive mission, user personas, every desired feature, priority, user journeys, success metrics and non-goals. |
| **[Technical Architecture](docs/ARCHITECTURE.md)** | Target monorepo, React/Next.js website, FastAPI service, Chrome/Edge extension, shared API, provider adapter, security, deployment and testing. |
| **[Roadmap & QA](docs/ROADMAP_AND_QA.md)** | Hard phase gates, current verified status, implementation priorities, test matrix, launch criteria and avoiding wasted Codex credits. |
| **[Competitors, Open Source & Licensing](docs/RESEARCH_AND_LICENSES.md)** | Links to reference repositories, market sites, reusable libraries, license diligence and research tasks. |

**The documents above are canonical.** A new developer should not need to read prior ChatGPT chats to understand the goal.

## Planned product pillars

| Pillar | Main outcomes |
| --- | --- |
| **Reliable core** | Safe URL handling, real authorized share metadata, file downloads, accurate errors, expiry detection, no fabricated quality/options. |
| **Excellent website** | Paste → inspect → preview → download; mobile-first design, embedded player, responsive folder browser and support for permitted batch/ZIP operations. |
| **Browser products** | Manifest V3 Chrome/Edge extension connected to the same backend and consistent UX. Future Firefox/PWA if justified. |
| **Great viewing** | Actual available video qualities, fullscreen, picture-in-picture, optional Continue Watching, bookmarks and history with privacy controls. |
| **Trust & operations** | Minimal permissions, security, accessibility, i18n, help/FAQ, privacy/copyright reporting, test automation and admin reliability/cost visibility. |
| **Future business** | Versioned API, optional accounts and premium entitlements, analytics, subscriptions and additional surfaces only after core readiness. |

## Run and develop the starter

See **[Local Development](docs/LOCAL_DEVELOPMENT.md)** for API, website and extension setup, and **[Ordered Implementation Checklist](docs/IMPLEMENTATION_CHECKLIST.md)** for the complete tracked roadmap. The website and extension source are development previews. API tests passed locally (20 cases); website builds and browser behavior still require CI/manual verification. The backend currently responds with `PROVIDER_NOT_CONFIGURED` for valid links rather than claiming downloads work.

## Immediate, non-negotiable first milestone

**Prove a reliable, compliant TeraBox integration with authorized test files before spending substantial time on cosmetic or premium features.**

1. Audit existing code and referenced projects.
2. Verify current provider terms, legitimate access methods and known limitations.
3. Demonstrate accurate file metadata and an authorized completed download.
4. Test expired, unsupported, protected and malformed links; protect against SSRF.
5. Only then implement the full website, player, folder workflows, browser extension and infrastructure.

A mock demo does **not** prove the real downloader works. If provider integration is not feasible under permissible access, document the blocker honestly.

## Architecture at a glance

```text
              Website (Next.js/React)
                        │
              Chrome/Edge extension
                        │
                        ▼
              Shared versioned API
                (Python FastAPI)
                        │
           Provider adapter / capabilities
                        │
           Permitted TeraBox integration
                        │
        File details · preview · download
```

One maintained monorepo; modular boundaries; only supported capabilities shown to users. Stack is a **proposal until the codebase is audited**, not a guarantee that it exists.

## Open-source combination strategy

Study **[TeraPlayer](https://github.com/gitmarcus07/Teraplayer)** as the primary architecture reference. Also evaluate **[Terabox-Web](https://github.com/Itz-Ashlynn/Terabox-Web)**, **[terabox-gateway](https://github.com/saahiyo/terabox-gateway)**, **[tera-peek](https://github.com/saahiyo/tera-peek)** and **[TeraBox Chrome extension](https://github.com/SH20RAJ/terabox-player-chrome-extension)** for selective compatible ideas.

Use maintained libraries rather than reinventing mature features where appropriate: **Video.js**, **hls.js** (only for real HLS), **Playwright**, and optional monitoring tools. Review **aria2/GPL** before any inclusion. Check current licenses, provenance, external proxies and dependencies; **do not blindly merge five projects**. See [research and licensing details](docs/RESEARCH_AND_LICENSES.md).

## Development stages

**G0:** repository/provider/license/competitor audit → **G1:** real permitted download proof → **G2:** complete core website + extension → **G3:** secure production release → **G4:** differentiated UX → **G5:** optional monetization and growth.

Keep truthful per-feature statuses: Not started, Implemented/unverified, Verified with mocks, Verified with authorized live test, Blocked, or Deferred. Every working claim should have dated test evidence.

## Safety, rights and affiliation

This is an **independent, unofficial project**, not affiliated with or endorsed by TeraBox. We build for files users own or have permission to access. Do not bypass authentication, access controls, provider restrictions, DRM or premium protections, and do not enable unauthorized distribution. Do not embed third-party cookies, credentials or untrusted demo proxy endpoints. Check current service terms and applicable law before public launch.

## For Codex or new contributors

**Begin with [AGENTS.md](AGENTS.md) and the documents linked above, inspect actual code, then work on G0/G1 before advanced features.** Do not reset an existing task or redo working code; use small testable milestones and report exactly what you verified.

*This README is intentionally complete enough to orient a developer at first glance; detailed requirements and acceptance criteria live in the linked documents.*
