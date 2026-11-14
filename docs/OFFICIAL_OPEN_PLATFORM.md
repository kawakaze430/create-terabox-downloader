# Official TeraBox Open Platform — implementation handoff

**Status:** OAuth client scaffold implemented and offline-tested; **NO live authorization, metadata or download has been verified**.
**GitHub blocker:** [#2](https://github.com/kawakaze430/create-terabox-downloader/issues/2).

## New verified research finding

TeraBox has an [official Open Platform integration site](https://www.terabox.com/integrations) and [developer documentation](https://www.terabox.com/integrations/docs?lang=en). Its [December 2024 product announcement](https://blog.terabox.com/terabox-december-2024-product-updates/) describes commercial integrations for storage, file access, transfer and sharing.

Documentation available in [Hindi](https://www.terabox.com/integrations/docs/hindi), [Chinese](https://www.terabox.com/integrations/docs/chinese) and other languages describes:

- Application owners **apply for** `client_id`, `client_secret`, `private_secret`; approval and commercial usage terms must be confirmed directly with TeraBox.
- Authorization-code or device-code workflows requiring real user consent. Browser authorization points to `https://www.terabox.com/wap/outside/login?clientId=...`.
- Fixed OAuth endpoints: `POST /oauth/gettoken`, `POST /oauth/refreshtoken`, `POST /oauth/tokeninfo` on `https://www.terabox.com`.
- A documented signature based on MD5 of `client_id_timestamp_client_secret_private_secret`. This is **only** a protocol compatibility signature; do not adopt MD5 for our own application security.
- Documented access-token lifetime of 2 days; refresh-token lifetime of 30 days, with a refresh token typically consumed on refresh.
- `tokeninfo` returns user-dependent regional `api_domain` and `upload_domain`. These values must **never** be treated as arbitrary trusted URLs.
- Documented file and share APIs: `/openapi/api/download`, `/openapi/share/verify`, `/openapi/share/list`, `/openapi/share/mediameta`, `/openapi/share/download` among others. **Endpoint presence alone does not prove a general anonymous public-link downloader is authorized or feasible.**

The documentation also restricts some app file operations to a designated `/From: Other Applications/...` storage area. Determine exact approved scopes and external-share rights before implementing them.

This replaces our earlier *incomplete research assumption* that no official-looking developer API documentation could be found. **It does not mean we currently have partner credentials, access or a functioning download engine.**

## Code introduced

`services/api/app/open_platform.py` is a standalone, credential-gated OAuth helper that is **not connected to FastAPI routes or the production ShareProvider**.

- `PartnerCredentials.from_environment()`: requires all three server-side credentials.
- `authorization_url(client_id)`: constructs TeraBox's documented authorization page without collecting user passwords.
- `oauth_signature(credentials, timestamp)`: implements the specified provider signature.
- `OpenPlatformOAuth.exchange_code()`, `refresh()`, `token_info()`: only known OAuth POST endpoints, no redirects, bounded responses and sanitized error texts.
- `OAuthTokens`: wraps tokens as Pydantic `SecretStr` to reduce accidental printing.
- `approved_api_origin(domain, approved_hosts)`: requires an explicit exact hostname allowlist for TeraBox-assigned regional domains. This is **validation only**, not a substitute for secure DNS resolution, pinned connections or egress firewall enforcement.

`services/api/tests/test_open_platform.py` uses only `httpx.MockTransport`; these are not live TeraBox tests. Nothing automatically makes network requests on import. No third-party repository code was copied.

## Apply for credentials

1. Use [TeraBox's official integration page](https://www.terabox.com/integrations) and its contact form (described in the TeraBox announcement).
2. Describe our own product, business/commercial use, browser extension, authorized files and public-share handling. Ask for **written confirmation of permitted scopes, download workflows, quotas, pricing, privacy/security requirements and production access**.
3. Obtain approved `client_id`, `client_secret`, `private_secret`; arrange a test account and operator-authorized share fixtures.
4. Store secrets only in deployment secret manager or local `.env` excluded from Git. **Never paste them into GitHub issues, CI logs, PRs, screenshots, or this chat.** A browser extension must never contain app secrets.
5. Verify the documented authorization callback behavior and secure `postMessage` origin/state verification. Build the full OAuth flow only when the partner agreement permits it.
6. Verify region-specific `api_domain` with TeraBox and explicitly approve each exact host; enforce HTTPS, private/reserved IP rejection, DNS-rebinding defense, no redirected secrets and outbound network controls.
7. Implement metadata and allowed download flow behind `ShareProvider`, with per-user consent, secure token storage/rotation, expiry handling and live tests.
8. Demonstrate **an actual completed authorized file transfer** before enabling download buttons or marking issue #2 complete.

## Local tests

From repository root:

```bash
python -m pip install -r services/api/requirements.txt
PYTHONPATH=services/api python -m pytest -q services/api/tests
```

CI also builds the website and checks the extension.

## Security / review caveats

- This is an **OAuth protocol adapter scaffold**, not a deployed authentication service. It has no public routes, no token persistence, no provider downloader and no frontend wiring.
- Injected `httpx.AsyncClient` should be created in production with `trust_env=False`, TLS validation, redirect prohibition, appropriate timeouts, and network egress controls; review for SSRF, proxies and DNS rebinding.
- Do not surface raw OAuth tokens or signed file URLs to untrusted clients.
- OAuth code exchange can only succeed with approved credentials and user authorization.
- TeraBox terms and partner API terms may further limit redistribution, bulk downloading, external link retrieval or monetization. Confirm with TeraBox rather than assuming.
