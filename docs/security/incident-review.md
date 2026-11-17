# Repository incident review

Reviewed 18 November 2026 (Asia/Kolkata) at `c0163c24ffdcf4391c0e2874cb508f52172958f1` in `sarfiaroui-oss/create-terabox-downloader`. Native Git advertised that exact commit as the default branch and sole remote branch. The initial checkout was clean, with 97 tracked files, 18 tracked subdirectories, and 51 reachable commits. Git object integrity passed. The merge tree is byte-identical to its second parent, `7b16ad8`; the merge itself added no file content. Commit author strings and unsigned commits cannot identify or authenticate the people who acted.

## Findings

- **Historical credential-like data confirmed.** Commit `05049dc` introduced the reference ZIPs. Commit `5dceb2d` moved and sanitized them. The two versions have identical member paths and order. Exactly three member contents differ: two previously populated session/cookie configuration fields and one captured page token. All three fields are empty in the current ZIPs. The original blobs remain reachable from Git history. Their validity, ownership and subsequent use are unknown.
- **Repository clutter has traceable Git provenance.** The reference uploads trace to `05049dc`. The vision traces to `35eb415`; the recovery grouping and inventories trace to `cf8417c`, `4d1c35e` and `08cffee`. Later engine, website and extension changes trace to `0a8117a`, `5b9ac57` and `f36a72b`. The repository evidence establishes these changes and their chronology. It does not establish that any were unauthorized.
- **Active execution review.** All tracked files across the reachable revisions have regular, non-executable Git modes. No tracked Git submodule, active custom hook, or CI path executing ZIP contents was observed. The active API uses its local disabled provider by default; the separate operator paths use explicit source admission and bounded requests. Website API traffic and the extension's validated site handoff matched their documented purposes. Common token, credentialed-URL and private-key patterns found no matches in 94 current and 133 historical-only unique text blobs. This limited check cannot establish absence of secrets or other indicators.
- **Workflow and dependencies.** The current three CI jobs run on ordinary main pushes and pull requests with `contents: read`; no archive execution or workflow secret use was observed. CI action tags are mutable. npm lock entries with download URLs used the npm registry and integrity hashes. Python dependencies use exact pins without hashes. Security tooling and package checks are recorded in the [baseline validation](../history/repository-reviews/baseline-validation-2026-11-18.md).
- **Metadata access.** The GitHub API repo/PR read returned a proxy CONNECT 403. GitHub PR approval, Actions history, audit events, collaborator and app grants, deploy keys, account sessions and branch rules could not be established from this workspace. A clean Git object check does not establish account security.

## Evidence preservation

Before edits, recorded remote and local refs, baseline tree paths and blob IDs, history, and working-tree status. A private full-history bundle and restored verification repository were created under `/workspace/scratch/terabox-incident.McAFyPAJ`, outside the checkout. The recovered baseline matched the full SHA and passed `git fsck`. Bundle SHA-256 is `44eff2ec2184450a218b57177256a9c90537afac2c12c18cc7c4922137ae104c`. The bundle contains the historical ZIPs and should remain private. Its restore test was local to this cloud machine; no independent private off-host storage was available.

| ZIP | Historical Git blob | Current sanitized Git blob |
| --- | --- | --- |
| TeraPlayer | `e53fc378354d04f69c6f31b6027d0d47c9b2a5c8` | `0f31c11fea1f9d9f31a1806c9918a52a738be6a0` |
| Gateway | `b8ce2056e5c801c750ad48ec692905b192ab0181` | `6421fa4aed81be43be47f9bbb2d172889551688d` |

See the [archive guide](../../research/archives/REFERENCE_ARCHIVES.md), [earlier security audit](recovery/SECURITY_AUDIT.txt) and [repository move ledger](../history/repository-reviews/move-ledger-2026-11-18.md).

## Owner actions

1. Treat the historical fields as potentially exposed. For accounts you control, revoke affected provider sessions and rotate any associated credentials where applicable. For third-party accounts, notify the responsible owner privately without copying values into a ticket or repository.
2. Verify GitHub security events, active sessions, personal access tokens, SSH/deploy keys, collaborators, installed applications, workflow runs, and rulesets in the account and repository UI. Preserve suspicious timestamps and event IDs before revoking unauthorized access. Confirm PR #5 and the reference uploads with the people who initiated them.
3. Keep main unchanged until account and repository write access are acceptable to the owner. Review history cleanup separately after revocation and evidence preservation. Published copies, forks and caches require separate consideration.
