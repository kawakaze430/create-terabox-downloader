# Preserved material for review

This folder keeps complete uploaded reference projects without placing them in the running application. No source project was silently discarded or merged.

| Location | Contents | Decision |
| --- | --- | --- |
| `archives/Teraplayer-main.zip` | Full TeraPlayer reference project, with uploaded session and captured page token values replaced by empty placeholders | Inspect individual ideas; do not execute its worker, cron or agent helper files as part of this app. |
| `archives/terabox-gateway-main.zip` | Full gateway reference project, with one uploaded cookie setting replaced by an empty placeholder | Inspect individual ideas; do not adopt its external worker or cookie flow as the product's provider. |
| `extracted/` | Local copies recreated by `python3 scripts/unpack_reference_archives.py` | Ignored generated material; the committed ZIPs and script reproduce it. |
| `future-ideas/PROJECT_IDEA_AND_FUTURE_VISION.txt` | Earlier detailed project idea, originally at the repository root | Preserved in full; the current roadmap is `PROJECT_VISION_AND_FUTURE_ROADMAP.txt`. |

Both projects include MIT licenses. Their presence does not establish that their advertised TeraBox downloads work or that their external-service paths are suitable for this product. See [the archive guide](archives/REFERENCE_ARCHIVES.md) and [the repository structure audit](recovery-notes/REPOSITORY_STRUCTURE_AUDIT_2026-11-17.md).

The [ZIP member inventory](archives/ZIP_MEMBER_INVENTORY.txt) names every nested file and folder in the two archives without exposing their contents.

The earlier uploaded ZIPs remain in Git history with populated cookie settings. If those sessions were valid, revoke them. The current archives are sanitized; no cookie value is printed or repeated in this repository documentation.
