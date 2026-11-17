# Uploaded reference archives

The repository contains two complete third-party projects as ZIP files. To unpack both into separate directories, run from the repository root:

```bash
python3 scripts/unpack_reference_archives.py
```

The checked-in ZIPs are preserved under `AnalyseFuture/archives/`. The command verifies each archive's SHA-256 and member CRC, rejects unsafe paths and symlinks, and creates `AnalyseFuture/extracted/Teraplayer-main/` and `AnalyseFuture/extracted/terabox-gateway-main/`. Rerunning it checks the extracted files without overwriting edits. `AnalyseFuture/extracted/` is ignored by Git because the ZIPs already preserve the source; run the command again in a new checkout. These directories are for inspection, not an application startup path.

The uploaded ZIPs contained populated cookie settings (`.dev.vars` in TeraPlayer and `.env.example` in gateway); TeraPlayer also included a captured page token in `cloudflare-worker/terabox-live.html`. The current archives and extracted copies replace those values with empty placeholders; the rest of both projects remains preserved. The earlier ZIP commit remains in Git history, so the owner should revoke any sessions represented by those settings. Do not run the archives' worker or helper scripts without reviewing them.

| Archive | Project languages and framework | Place in this repository |
| --- | --- | --- |
| `Teraplayer-main.zip` | Python FastAPI backend, React/JavaScript frontend, browser extension | Product and UI reference. Its provider extraction depends on third-party services or sessions and has not been integrated. |
| `terabox-gateway-main.zip` | Python Flask/aiohttp service | Provider and failure-handling reference. Its external worker and cookie paths have not been integrated. |

Both archives contain MIT license files. Before adapting individual files, preserve their notices and review the component's behavior. The existing product uses Python FastAPI for the shared API, TypeScript Next.js for the website, and a small JavaScript browser extension. They communicate through the versioned JSON API. Moving everything to one language would require replacing tested components and would not establish authorized provider access. See [architecture](../../docs/ARCHITECTURE.md) and [source audit](../../docs/RESEARCH_AND_LICENSES.md).
