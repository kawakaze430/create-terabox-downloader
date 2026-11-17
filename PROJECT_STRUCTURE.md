# Project structure

One FastAPI service supports a Next.js website and a Manifest V3 extension. The download engine lives in the API service with its own CLI and tests. The engine accepts already authorized direct sources. The share-link provider remains disabled by default.

```text
.
├── .github/workflows/             CI for the API, web, and extension
├── apps/
│   ├── web/                       Next.js app, contracts, and browser tests
│   └── extension/                 MV3 popup, parser, settings, and tests
├── services/api/
│   ├── app/                       FastAPI, provider boundaries, and transfer engine
│   └── tests/                     Service, egress, engine, and CLI tests
├── scripts/                       Benchmark, packaging, and archive tools
├── docs/
│   ├── history/repository-reviews/ Dated inventories, moves, and recovery reports
│   ├── security/
│   │   └── recovery/              Earlier security and structure findings
│   └── ...                        Product, development, operations, and handoff
└── research/
    ├── archives/                  Sanitized reference ZIPs and member inventory
    └── future-ideas/              Earlier product concepts
```

The API owns share-link admission and versions its HTTP contract. The extension uses a separate local parser before handing a link to the website. The engine owns streaming, retries, Range recovery, verification and atomic publication. Upstream authorization and source policy belong in the provider/operator code. Keep package locks and tests with the application they support.

Start with the [documentation index](docs/README.md), [current work](docs/CODEX_CONTINUITY.md) and [baseline inventory](docs/history/repository-reviews/baseline-inventory-2026-11-18.md). The [move ledger](docs/history/repository-reviews/move-ledger-2026-11-18.md) maps the earlier paths. The [incident review](docs/security/incident-review.md) records evidence and owner actions.

The [reference archives](research/archives/REFERENCE_ARCHIVES.md) have no runtime or CI consumers. Optional inspection can recreate copies under the ignored `research/extracted/` directory. Local virtual environments, `node_modules/`, Next.js output, Python caches, and test reports are also ignored.
