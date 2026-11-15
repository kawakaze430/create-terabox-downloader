# P0 Provider Feasibility and Safety Review

**Updated:** 2026-11-16. **Status:** Real TeraBox integration remains **blocked and unverified**.
**Tracking:** [Issue #2](https://github.com/kawakaze430/create-terabox-downloader/issues/2).

## What has and has not been established

The [TeraBox Terms of Service](https://www.terabox.com/terms/duty) restrict bypassing authentication/security, access to areas where the user is not authorized, and scraping outside publicly supported interfaces. The terms also require appropriate rights to download content. These are material commercial-launch constraints, not a blanket authorization to use unofficial APIs.

The initial 2026-11-13 research pass did not locate an official cloud-file API. **This finding was superseded:** TeraBox's [Open Platform guide](https://www.terabox.com/integrations/docs?lang=en) documents partner OAuth, regional API host discovery, and file/share metadata/download endpoints. However, no partner credentials, approved public-share scopes, authorized live metadata or completed file transfer have been verified. See [official integration](OFFICIAL_OPEN_PLATFORM.md) and [operator validation](OPERATOR_VALIDATION.md).

**Domain warning:** \`teraabox.com\` (with two 'a' letters) offers a *separate link management/shortening API*. It is not evidence of a TeraBox cloud-file developer API; do not merge or trust similarly named products without checking their operator.

Community repositories that use shared cookies, unknown proxies, transient links or reverse-engineered endpoints are references for research, **not approved, production-ready dependencies**.

## This PR implements

- Strict \`ShareResolution\` / \`SharedFile\` / \`Capabilities\` model boundaries.
- Deterministic, structured \`ProviderErrorCode\` categories with safe client messages.
- Dependency-injected provider seam so **offline** tests can simulate metadata/errors.
- API contract validation that forbids leaking arbitrary upstream fields such as cookies and raw direct links.
- \`GET /readyz\`: 503 until a configured provider is present, separate from \`/healthz\` liveness.
- No outbound HTTP integration and **no download URL generation**, by design.

## Before enabling real provider calls

1. Confirm a permitted integration and acceptable operating terms for independent/commercial use, preferably directly with TeraBox.
2. Audit the five referenced repositories' actual code, licenses, reliance on cookies/workers/proxies, and live reliability. Do not copy code without permission.
3. Supply test URLs to **non-sensitive files owned or authorized by the operator**: small file, large file, video, folder and expired/removed share. Never put credentials or sensitive shares in public PRs.
4. Design constrained outbound HTTP transport: TLS, exact host allowlists, bounded redirects, DNS and IP validation **without DNS-rebinding gaps**, egress firewall rules, timeouts, budgets and logging redaction.
5. Implement supported metadata and download handoff behind the provider protocol only when lawful access is verified. Add test evidence for a **completed file transfer**, expiry errors, protected links, upstream changes, rate limits and resource cost.
6. When a provider cannot be confirmed, preserve \`UnconfiguredProvider\` (501 on resolve, 503 readiness); do not present a mock as working.

## Review requests for Codex

- Verify contract shape can represent legitimate metadata without exposing protected URLs.
- Review Pydantic validation constraints and whether error codes/status are appropriate for future integrations.
- Add provider-specific outbound security only **with** a concrete approved endpoint, because DNS preflight alone is insufficient protection against SSRF/rebinding.
- Continue issue #2 after this PR is reviewed; keep speculative premium UI work deferred.
