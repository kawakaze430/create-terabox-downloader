"""Build a reproducible, minimal MV3 ZIP without changing checked-in config."""

import argparse
import json
from pathlib import Path
import subprocess
from zipfile import ZIP_DEFLATED, ZipFile, ZipInfo


ROOT = Path(__file__).resolve().parents[1]
FILES = (
    "config.mjs",
    "links.mjs",
    "manifest.json",
    "popup.css",
    "popup.html",
    "popup.js",
)


def package_extension(output: Path, website_origin: str | None = None) -> str:
    source = ROOT / "apps" / "extension"
    if output.suffix != ".zip" or source == output.resolve() or source in output.resolve().parents:
        raise ValueError("Choose a .zip output outside apps/extension")
    contents = {}
    for name in FILES:
        path = source / name
        if path.is_symlink() or not path.is_file():
            raise ValueError("Extension package input must be a regular file")
        contents[name] = path.read_bytes()
    manifest = json.loads(contents["manifest.json"])
    if (
        manifest.get("manifest_version") != 3
        or manifest.get("permissions") != ["activeTab"]
        or any(manifest.get(key) for key in ("host_permissions", "optional_host_permissions", "optional_permissions"))
    ):
        raise ValueError("Extension package must retain the reviewed MV3 activeTab-only permissions")
    # Reuse the runtime validator: packaging and navigation accept identical origins.
    # Arguments are passed without a shell; the origin is never executable code.
    code = (
        f"import {{ normalizeWebsiteOrigin }} from {json.dumps((source / 'links.mjs').as_uri())};\n"
        f"import {{ WEBSITE_ORIGIN }} from {json.dumps((source / 'config.mjs').as_uri())};\n"
        "process.stdout.write(normalizeWebsiteOrigin(process.argv.length > 1 ? process.argv[1] : WEBSITE_ORIGIN));"
    )
    command = ["node", "--input-type=module", "-e", code]
    if website_origin is not None:
        command.append(website_origin)
    try:
        origin = subprocess.run(command, check=True, capture_output=True, text=True).stdout
    except subprocess.CalledProcessError as error:
        raise ValueError("Invalid website origin; use an HTTPS origin or exact local development origin") from error
    contents["config.mjs"] = (
        "// Build-time website destination; contains no credentials.\n"
        f"export const WEBSITE_ORIGIN = {json.dumps(origin)};\n"
    ).encode()
    output.parent.mkdir(parents=True, exist_ok=True)
    with ZipFile(output, "w", compression=ZIP_DEFLATED, compresslevel=9) as archive:
        for name in sorted(contents):
            info = ZipInfo(name, date_time=(1980, 1, 1, 0, 0, 0))
            info.compress_type = ZIP_DEFLATED
            info.create_system = 3
            info.external_attr = 0o100644 << 16
            archive.writestr(info, contents[name], compresslevel=9)
    return origin


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--website-origin", help="Owned HTTPS origin; defaults to checked-in local development origin")
    parser.add_argument("--output", type=Path, default=ROOT / "dist" / "cloudlink-extension.zip")
    args = parser.parse_args()
    try:
        origin = package_extension(args.output, args.website_origin)
    except (ValueError, OSError) as error:
        parser.exit(1, f"Packaging failed: {error}\n")
    print(f"Packaged extension: {args.output}; destination: {origin}")


if __name__ == "__main__":
    main()
