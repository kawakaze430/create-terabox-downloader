# Extension development and packaging

The Chrome/Edge Manifest V3 popup uses `activeTab` to check the current page. It opens the configured website with a supported share link prefilled, or opens its homepage so an authorized operator can access managed downloads. Only the normalized supported share is passed to the website, in a URL fragment that the page clears.

## Local installation

1. Start the website and API using [LOCAL_DEVELOPMENT.md](LOCAL_DEVELOPMENT.md).
2. In Chrome, open `chrome://extensions`; in Edge, open `edge://extensions`. Enable Developer mode, choose **Load unpacked**, and select `apps/extension`.
3. Open a supported share page, activate the extension, and choose **Open share in CloudLink**. The parser fixture `https://terabox.com/s/1Abc_123` exercises the share format.
4. Verify the website input is populated and the fragment clears. Repeat on an unsupported page and select **Open CloudLink**. The website should open at its homepage without the current tab's URL.

`apps/extension/config.mjs` defaults to `http://localhost:3000`. The popup validates configuration before querying the active tab and computes the destination from that validated origin. Invalid configuration disables the action. A failed tab open produces a retry message.

## Build an owned-site package

From the repository root, with Python 3.12+ and Node 22+ available:

```bash
python3 scripts/package_extension.py \
  --website-origin https://your-owned-domain.example \
  --output dist/cloudlink-extension.zip
```

Replace the example with a domain you control. The build writes its selected origin only into `config.mjs` inside the ZIP; checked-in development configuration is unchanged. No environment file or secret is embedded. Without `--website-origin`, the package uses the checked-in local development setting. A local package is for development, not store submission.

Allowed destinations are an ASCII HTTPS hostname/IPv4 origin with no non-default port (explicit `:443` is normalized), or exactly `http://localhost:3000` / `http://127.0.0.1:3000` for development. Supply an origin without a trailing slash. Credentials, paths, query strings, fragments, escapes, malformed hostnames, and other HTTP destinations/ports are rejected. IPv6 and internationalized hostname syntax are not accepted by this small configuration format. The website destination is a build setting; a visited share page cannot choose it.

The ZIP has a fixed six-file allowlist, sorted entries, fixed timestamps and permissions, and repeatable compression on the same Python/zlib toolchain. Tests, docs, dependencies and caches are excluded. The packager rejects source symlinks and unreviewed extension permission changes. It retains Manifest V3 and `activeTab` only. It does not sign or publish a store release.

Unzip to a fresh directory and load that directory unpacked to inspect a release candidate. Verify the chosen HTTPS site, popup behavior, and fragment consumption in actual Chrome and Edge before release. Complete the owner's branding, privacy, permission, support and store-account review separately.

## Automated checks

```bash
node --check apps/extension/popup.js
node --test apps/extension/tests/*.test.mjs
```

The suite covers share parsing, destination rejection/canonicalization, private-query removal, fragment handoff, and deterministic minimal packaging. Packaging tests invoke Python and Node without network access. These checks do not prove an installed Chrome/Edge extension or a live TeraBox transfer works; record those manual/authorized checks separately.
