# Competitive Research, Reference Repositories, Dependencies & Licensing

**Updated:** 2026-11-13  
**Status:** Research backlog. Mentioning a source here does not mean its code has been audited, reused, or verified to work.

## Why references matter

We intend to build an **original, maintainable product** using proven ideas and legally compatible components rather than blindly combining five full applications. A competitive feature is not necessarily technically feasible or permitted by the provider. Engineers must distinguish an upstream limitation from a defect in our app.

## Reference applications to audit

| Reference | Intended research scope | Licensing / integration action |
| --- | --- | --- |
| [gitmarcus07/Teraplayer](https://github.com/gitmarcus07/Teraplayer) | Main architectural reference: site, API, extension, folders, ZIP, player | Verify the license from current commit; audit each component, tests and upstream assumptions before reuse. |
| [Itz-Ashlynn/Terabox-Web](https://github.com/Itz-Ashlynn/Terabox-Web) | Responsive React UI and share processing experience | Check license and provenance; use patterns when reuse is not permitted. |
| [saahiyo/terabox-gateway](https://github.com/saahiyo/terabox-gateway) | Provider adapter, metadata, streaming and backend mechanics | Evaluate cookies, tokens, worker/proxy dependencies; verify permitted access and license. |
| [SH20RAJ/terabox-player-chrome-extension](https://github.com/SH20RAJ/terabox-player-chrome-extension) | Browser page detection, video playback, extension UX | Audit Manifest version, permissions, origin handling, update health, license. |
| [saahiyo/tera-peek](https://github.com/saahiyo/tera-peek) | Metadata, thumbnail, video-preview and Next.js UX | Audit demo-worker dependence, license and current provider compatibility. |
| [SarangGit/TeraDLDW](https://github.com/SarangGit/TeraDLDW) | Additional Flask + vanilla UI approach | Optional reference only; avoid importing redundant frameworks. |
| [Paidguy/terabox-api](https://github.com/Paidguy/terabox-api) | Optional Cloudflare Workers implementation | Evaluate provenance, access authorization, security and longevity. |
| [0xarchit/Terabox-Downloader](https://github.com/0xarchit/Terabox-Downloader) | Historical upstream compatibility issues | Do not select as foundation without verifying current function. |

Prior discussions described some repositories as MIT-licensed, but **do not rely on old descriptions**. Check each current LICENSE, file-level notices, dependencies and potential copied code before reuse. Unlicensed repository content is *not* automatically open-source for copying.

## Market and feature benchmarking

Candidates: [iTeraPlay](https://iteraplay.com), [TeraDownloader](https://teradownloader.com), [TeraGrab](https://teragrab.com), [TeraPlayer](https://teraplayer.in), [TeraLoader](https://teraloader.com).

Assess with dated screenshots and own authorized test shares:
- Flow from paste → metadata → preview → download.
- Real (not advertised) support for folders, multi-file/ZIP, alternate qualities, temporary links, failure recovery and extension integration.
- Video controls: fullscreen, picture-in-picture, subtitles, Continue Watching, bookmarks.
- UI speed, mobile usability, accessibility, localization, privacy, tracking, support and transparency.
- Operating limits, authentication, premium gating, account features and actual costs.

Do not infer market leadership from a single traffic screenshot or marketing claim. Do not present third-party feature listings as tested capabilities. A market benchmark document with date, test condition and evidence should be produced before making competitive claims.

## Libraries to evaluate (not automatically install)

| Library/tool | Intended value | Key review before adoption |
| --- | --- | --- |
| [Video.js](https://github.com/videojs/video.js) | Accessible, mature player controls and plugin ecosystem | Browser support, build size, version license, maintainability. |
| [hls.js](https://github.com/video-dev/hls.js) | HLS playback where a legitimate stream is actually offered | Do not assume provider supplies HLS; confirm integration and license. |
| [Playwright](https://github.com/microsoft/playwright) | Browser E2E and smoke testing | Scope to local/staging site and authorized fixtures; manage resources. |
| [Sentry SDK](https://github.com/getsentry/sentry-javascript) | Error monitoring | Data processing, privacy redaction, cost and vendor dependency. |
| [aria2](https://github.com/aria2/aria2) | Download/resume techniques | GPL licensing can impose obligations: do not embed/distribute without dedicated review. Prefer standards/browser functionality. |
| [ffmpeg.wasm](https://github.com/ffmpegwasm/ffmpeg.wasm) | Optional browser video processing | Only implement with proven user need and rights; size, performance, license. |

Favor mature libraries, minimal bundles, pinned versions, dependency scanning, compliance attribution and documented replacement paths. Avoid dependencies added only to imitate a competitor.

## Licenses, rights, branding and provider compliance

- Keep the project owner's original source, distinctive brand, graphics and hosting configurations separately documented.
- Preserve copyright notices and third-party licenses for reused code. Add `THIRD_PARTY_NOTICES.md` when material is actually imported.
- A publicly viewable GitHub repository is not automatically permission to copy.
- Do not take other sites' graphics, trademarks, proprietary text or protected source.
- Access only authorized public shares or the user's own authorized files. Do not defeat login, CAPTCHA, DRM, premium restrictions or access controls.
- Verify TeraBox's current terms and integration possibilities with suitable legal review before commercial release.
- Never import third-party users' cookies, session credentials or hardcoded secrets; do not route production traffic through untrusted demo proxies.
- Test and document actual upstream response and breakage; recognize that third-party APIs can disappear overnight.

## Research deliverables for the first Codex milestone

1. Table of reference repos with license URL, commit audited, last activity, major dependencies, security issues, features present, actual test results and a reuse/rewrite/ignore verdict.
2. Benchmark matrix for competitors with observation dates, screenshots or reproduced authorized test evidence, and explicit unknowns.
3. Provider feasibility finding: compliant data access methods, unsupported operations, temporary URL expiry, bandwidth and upstream rate limits.
4. Dependency evaluation: why each extra library is needed, its exact license and compatibility, maintenance signals, size and security.
5. Explicit architecture decision with risks and first implementation milestones.
