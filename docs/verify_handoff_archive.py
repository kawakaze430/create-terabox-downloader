"""CI integrity check for the public project continuity Word DOCX (stdlib only)."""
from pathlib import Path
from zipfile import ZipFile, is_zipfile
import xml.etree.ElementTree as ET

ROOT = Path(__file__).resolve().parent.parent
DOCUMENT = ROOT / "docs" / "PROJECT_MASTER_HANDOFF.docx"
W = "{http://schemas.openxmlformats.org/wordprocessingml/2006/main}"
REL = "{http://schemas.openxmlformats.org/package/2006/relationships}"

if not is_zipfile(DOCUMENT):
    raise SystemExit("Project handoff DOCX is not a valid ZIP package.")

required = {
    "[Content_Types].xml",
    "_rels/.rels",
    "word/document.xml",
    "word/styles.xml",
    "word/_rels/document.xml.rels",
    "docProps/core.xml",
    "docProps/app.xml",
}
with ZipFile(DOCUMENT) as archive:
    if required - set(archive.namelist()):
        raise SystemExit("Project handoff DOCX is missing required Office XML files.")
    bad = archive.testzip()
    if bad:
        raise SystemExit("DOCX ZIP checksum failed.")
    for name in required:
        if name.endswith((".xml", ".rels")):
            ET.fromstring(archive.read(name))
    doc = ET.fromstring(archive.read("word/document.xml"))
    content = " ".join(node.text or "" for node in doc.iter(W + "t"))
    for expected in (
        "Permanent Project Handoff",
        "Project Chat History",
        "BEGIN NOW.",
        "TOTAL GITHUB REPOSITORIES: 49",
        "TeraPlayer",
        "TeraBox Gateway",
        "PROVIDER_NOT_CONFIGURED",
    ):
        if expected not in content:
            raise SystemExit(f"Missing essential archived topic: {expected}")
    rels = ET.fromstring(archive.read("word/_rels/document.xml.rels"))
    hyperlinks = [
        e for e in rels.iter(REL + "Relationship")
        if e.attrib.get("Type", "").endswith("/hyperlink")
    ]
    if len(hyperlinks) < 49 or any(
        not e.attrib.get("Target", "").startswith(("https://", "http://"))
        for e in hyperlinks
    ):
        raise SystemExit("Project handoff is missing external research hyperlinks.")
print("DOCX archive validated: Office XML, 49+ links, full prompt, project history.")
