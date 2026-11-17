# Managed downloads

Managed downloads let an operator register permitted HTTPS files and grant access to trusted users. The website signs in with an operator-provisioned key, lists approved files, reports progress, and verifies the completed file against the registry's size and SHA-256 before saving it.

The managed catalog and the TeraBox share resolver have separate source policies. Public TeraBox resolution remains disabled pending an authorized live verification. See the [TeraBox operator runbook](OPERATOR_VALIDATION.md).

## Register a source

Use an HTTPS source you control or have permission to serve. Record size and SHA-256 through a trusted copy, confirm the exact source host, and put the file in a private JSON registry. This example uses a public README pinned to a revision of this project.

```json
{
  "allowed_hosts": ["raw.githubusercontent.com"],
  "sources": [
    {
      "source_id": "project-readme",
      "name": "project-readme.md",
      "url": "https://raw.githubusercontent.com/sarfiaroui-oss/create-terabox-downloader/c0163c24ffdcf4391c0e2874cb508f52172958f1/README.md",
      "size_bytes": 11078,
      "sha256": "90ba2d5ad39d0e9a9ff62308ec5588df845550350f87b10ef190593086dfb9dd"
    }
  ]
}
```

The app accepts up to 32 registered files of up to 16 MiB each. Source references and digests come from the operator's registry. The source URL stays in the API process. The engine requires direct DNS and TLS access to an approved public address and rejects redirects. A request that works through a platform HTTP proxy can still fail this direct check.

## Run on a Linux host

The managed service uses one API worker per private storage directory. Give the registry file and storage directory to that OS user with modes `0600` and `0700`, respectively. Supply a high-entropy access key of at least 32 URL-safe characters through the API's private runtime environment. Generate it with `secrets.token_urlsafe(32)`. The key belongs on the server and with the people authorized to use that catalog.

| Setting | Purpose |
| --- | --- |
| `TRANSFER_REGISTRY_PATH` | Absolute path to the private source registry. The API registers managed routes when this is set. |
| `TRANSFER_STORAGE_DIR` | Absolute path to a precreated private storage directory. |
| `TRANSFER_ACCESS_KEY` | Shared catalog sign-in key. Each sign-in creates its own expiring session. |
| `ALLOWED_ORIGINS` | Exact site origin, such as `https://files.example.net` or `http://127.0.0.1:3000` for loopback development. |
| `NEXT_PUBLIC_ENABLE_MANAGED_TRANSFERS=1` | Build-time switch for the website's managed download UI. |
| `NEXT_PUBLIC_API_BASE_URL` | Exact HTTPS API origin. Use an explicitly empty value for same-origin reverse proxying, or `http://127.0.0.1:8000` for separate loopback services. |

Run Uvicorn with one worker. Use `--no-access-log` and bind to loopback for local development. Behind a reverse proxy, trust forwarding headers only from that proxy's private address. Sessions and jobs are process-local. A restart invalidates them and clears abandoned job files. Sign-out revokes the session. The API limits active sessions, jobs, retries, file delivery concurrency, and file lifetime. Add ingress quotas and aggregate monitoring before expanding beyond a trusted group. Keep access keys, session tokens, and upstream URLs out of request logs.

## Container deployment

The [base Compose file](../deploy/compose.yaml) runs a single API worker, the built Next.js website, and a Caddy ingress. Start the base stack for a loopback smoke at port 8080.

```bash
docker compose -f deploy/compose.yaml up --build --wait
curl -fsS http://127.0.0.1:8080/healthz
curl -fsS http://127.0.0.1:8080/ -o /dev/null
```

For an owned deployment, set the public domain and ingress values from the [example](../deploy/.env.example). Point DNS at the host, allow ports 80 and 443, and provide the path to a private runtime env file containing `TRANSFER_ACCESS_KEY`. The [managed overlay](../deploy/compose.managed.yaml) uses a private named volume for the registry and transfer storage.

```bash
compose=(docker compose -f deploy/compose.yaml -f deploy/compose.managed.yaml)
"${compose[@]}" build
"${compose[@]}" run --rm --no-deps -T api sh -ec '
  umask 077
  registry=$(mktemp /var/lib/transfers/registry.XXXXXX)
  trap "rm -f \"$registry\"" EXIT
  cat >"$registry"
  mv "$registry" /var/lib/transfers/registry.json
' < /absolute/private/sources.json
"${compose[@]}" up -d --wait
```

Confirm the deployed HTTPS page and `/healthz`. Sign in with the operator-provisioned access key, download the registered file, and compare its SHA-256 with the independent source digest. Test cancellation and sign-out, then [package the extension](EXTENSION_DEVELOPMENT.md#build-an-owned-site-package) for that same site.

## Acceptance checks

Set `python` on `PATH` to the API virtual environment. Run from `apps/web` with ports 3000 and 8000 free.

```bash
export NEXT_PUBLIC_ENABLE_MANAGED_TRANSFERS=1
export NEXT_PUBLIC_API_BASE_URL=http://127.0.0.1:8000
npm run build
npm run typecheck
npm run test:e2e -- managed-transfers.spec.ts
npm run test:e2e -- --config playwright.managed.config.ts
```

The dedicated configuration starts real FastAPI, engine, and Next.js processes, then downloads and hashes fixed test bytes in desktop and mobile Chromium. Its default uses a test-only source transport. In Codex Cloud, set `TMPDIR=/workspace/scratch` for the temporary test registry and storage.

Run `MANAGED_E2E_LIVE=1 npm run test:e2e -- --config playwright.managed.config.ts` on a runner with direct DNS and TLS egress to exercise the commit-pinned GitHub source through the production transport. Once the updated workflow is available for manual dispatch, **Platform CI** can run the same live check.
