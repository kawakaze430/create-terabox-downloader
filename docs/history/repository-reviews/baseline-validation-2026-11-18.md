# Baseline verification

Inspected `c0163c24ffdcf4391c0e2874cb508f52172958f1` on 18 November 2026. The initial Git status was clean. Cloud Linux ran Python 3.12.14, Node 24.22.1, npm 11.9.0, and system Chromium 156.0.8078.79.

Before testing, reviewed the tracked file modes, workflow commands and permissions, Python and npm manifests and locks, app and test entry points, browser test servers, shell and subprocess usage, extension packager, benchmark, and archive validators. The npm lock points to the public npm registry, includes integrity for each resolved entry, and declares no package install scripts. The Python lock pins package versions and contains no direct URL or alternate package index. The DOCX has seven XML members and no VBA or embedded executable objects. The benchmark maps only the fixture host to a local server through an injected test transport.

| Scope and command | Observed result |
| --- | --- |
| `services/api/.venv/bin/python -m pip install -r services/api/requirements.lock` and `python -m pip check` in the API environment | Pass. All pinned requirements present and compatible. |
| `PYTHONPATH=services/api services/api/.venv/bin/python -m pytest -q -ra services/api/tests` | 250 passed, 0 failed, 0 skipped. Starlette warned about the deprecated TestClient integration with httpx. |
| Same pytest command scoped to `test_download_engine.py` and `test_download_cli.py` | 77 passed, 0 failed, 0 skipped. These tests are included in the 250 above. |
| `node --check apps/extension/popup.js` and `node --test apps/extension/tests/*.test.mjs` | Syntax passed. 50 passed, 0 failed, 0 skipped. Package tests independently checked the ZIP file list, deterministic bytes, permission limits, and preservation of the checked-in configuration. |
| Read `apps/extension/manifest.json` and assert Manifest V3, exactly `activeTab`, and no optional permissions or host permissions | Pass. |
| `npm ci --no-audit --no-fund`, `npm run build`, and `npm run typecheck` from `apps/web` | Pass. Next.js built the root page and TypeScript checked cleanly. |
| `CI=1 PLAYWRIGHT_CHROMIUM_EXECUTABLE_PATH=/usr/bin/chromium npm run test:e2e` with the API virtual environment on PATH | 20 passed, 0 failed, 0 skipped, across desktop and mobile. Stale onboarding processes initially occupied ports 3000 and 8000. After those owned processes stopped, Playwright started fresh Next.js and Uvicorn services. Chromium came from the image, so the Playwright browser download was unnecessary. Node printed a harmless NO_COLOR/FORCE_COLOR warning. |
| `python3 docs/verify_handoff_archive.py` | Pass. Word XML, the project prompt and history, and 49 or more research hyperlinks validated. |
| `PYTHONPATH=services/api services/api/.venv/bin/python -m app.preflight` | Expected unconfigured preflight result. The public provider was disabled and live verification was false. |
| `services/api/.venv/bin/python scripts/benchmark_download_engine.py --size-mib 4 --repeats 3` | 9 verified samples using real loopback bytes. The 4,194,304-byte payload matched independent SHA-256 validation in all samples. A clean stream used one attempt. Interrupting after 524,288 bytes used two attempts. Restart transferred 4,718,592 body bytes, and Range recovery transferred 4,194,304. |
| Verify archive SHA-256 and invoke `check_entries` from `scripts/unpack_reference_archives.py` | Both archive checksums and all 341 entry safety/CRC checks passed. No third-party archived scripts ran. |
| `npm audit --json` from `apps/web` | npm reported zero known advisories. |
| `pip-audit` 2.10.1 installed from PyPI in a temporary environment, then `python -m pip_audit --disable-pip --no-deps --requirement services/api/requirements.lock` | PyPI reported zero known advisories against the pinned full lock. The tool warned that the pins are unhashed. |

Engine coverage includes streamed and declared size limits, checksum and exact size verification, retry and wait bounds, upstream failures, redirect rejection, Range and strong ETag recovery, verified publication, cancellation and partial-file cleanup. API tests cover parser and provider contracts, OAuth and operator probes with mocked provider transport, bounded inputs and responses, concurrency, safe DNS/egress and CORS. Browser checks used the actual local API for supported and unsupported link handling and provider-unavailable behavior. Metadata, outage and delayed-response cases used controlled Playwright routes. Extension browser APIs were mocked in the 50 automated tests.

Live TeraBox and operator authentication were not run. Release publication and Chrome/Edge toolbar activation were not exercised. Third-party ZIP reconstruction was not performed on the baseline checkout. Dependency advisory checks reflect the queried services and time. Reported transfers use a controlled fixture.

Installed extension verification was blocked. In a disposable Chromium profile, the browser rejected `Extensions.loadUnpacked` with “Loading of unpacked extensions is disabled by the administrator.” The mocked extension tests, manifest check and packaging tests passed independently.
