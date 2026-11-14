# Run the Development Foundation

**Development-only starter.** Real TeraBox metadata, previews and downloads are not implemented. The API intentionally returns HTTP 501 PROVIDER_NOT_CONFIGURED for recognized links.

## Requirements
- Python 3.12+ and a local virtual environment
- Node.js 22+ and npm
- Chrome or Edge for manually loading the unpacked extension

## Start API
From repository root:

    cd services/api
    python -m venv .venv
    source .venv/bin/activate        # Windows: .venv\Scripts\activate
    python -m pip install -r requirements.txt
    python -m uvicorn app.main:app --reload --host 127.0.0.1 --port 8000

Open http://127.0.0.1:8000/docs for generated OpenAPI docs.
The local API allows CORS for http://localhost:3000 and http://127.0.0.1:3000, configurable by ALLOWED_ORIGINS. Restrict production origins.

## Start web app
In a second shell:

    cd apps/web
    cp .env.example .env.local       # Windows: copy .env.example .env.local
    npm ci
    npm run dev

Open http://localhost:3000. The interface validates supported share URL shapes with the API. "Check downloader status" reports that a live provider is not configured.

## Extension (unpublished developer proof)
Chrome/Edge → Extensions → Developer mode → Load unpacked → select apps/extension.
Open a supported TeraBox public share, click the extension icon, and then "Open in website".
The extension opens localhost:3000 and pre-fills the share link. It does **not** download content, request cookies or interact with other tabs. Localhost is hard-coded in this development-only build; replace it with an independently owned production domain before release.

## Tests
From repository root:

    python -m pip install -r services/api/requirements.lock
    PYTHONPATH=services/api python -m pytest -q services/api/tests   # bash/macOS
    node --check apps/extension/popup.js

Next.js build verification requires npm ciation:

    cd apps/web && npm ci && npm run build

No actual remote TeraBox API request is made in any parser test. Passing mocked tests does not establish download functionality.

## API contract

- GET /healthz — service operational but provider not configured
- POST /api/v1/shares/validate — JSON: {"url": "https://terabox.com/s/1Abc_123"}; returns format validation and normalized URL
- POST /api/v1/shares/resolve — same input; valid link currently returns HTTP 501 with error.code PROVIDER_NOT_CONFIGURED
- Invalid link returns HTTP 400 error object; unsupported host returns UNSUPPORTED_HOST.

Supported hosts are explicitly allowlisted in services/api/app/links.py and must be reviewed periodically. Only the /s/{token} and /sharing/link?surl={token} formats are recognized in this starter.

## Before production
- Obtain and verify a permitted provider integration; do not embed untrusted proxy/cookie credentials.
- Review CORS, ingress/egress, redirect/DNS SSRF security and rate limits.
- Add locked dependency manifests and dependency/security scanning.
- Replace the local extension destination with configurable published website, test extension behavior, and publish privacy terms.
- Add deployment, operational monitoring and legal review.
- Follow docs/IMPLEMENTATION_CHECKLIST.md in order.

## Repeatable browser checks

Install API dependencies above and run `npm ci` in `apps/web`, then:

```bash
npm run build
npx playwright install chromium
npm run test:e2e
```

Playwright starts both the production web build and local API. Ensure `python`
uses the API virtual environment. For a preinstalled Chromium, set
`PLAYWRIGHT_CHROMIUM_EXECUTABLE_PATH=/usr/bin/chromium`. Both desktop and mobile
viewports exercise the real validation API; the live provider stays disabled.
Extension checks: `node --test apps/extension/tests/*.test.mjs` from the repo root.

### API limits and privacy

See `services/api/.env.example` for body, timeout, concurrency and rate limits.
The limiter uses the ASGI peer address, never raw `X-Forwarded-For`; only configure
Uvicorn trusted proxy IPs for your actual proxy. Limits are per process, so apply
aggregate quotas at your ingress for multiple replicas. No private share URL or
upstream exception text is emitted by application error handlers. Disable access
logging (`--no-access-log`) and review hosting/proxy logs before using real shares.
The extension fragment handoff is cleared after reading; manually supplied legacy
query links can still reach hosting access logs before the page clears them.
