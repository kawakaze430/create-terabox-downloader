"""Recreate isolated reference source trees from the two checked-in ZIPs."""

from hashlib import sha256
from pathlib import Path, PurePosixPath
import shutil
import stat
import tempfile
from zipfile import ZipFile


ROOT = Path(__file__).resolve().parents[1]
ARCHIVE_DIR = ROOT / "research" / "archives"
OUTPUT = ROOT / "research" / "extracted"
ARCHIVES = {
    "Teraplayer-main.zip": (
        "Teraplayer-main",
        "4b06f6e36ff45d12b51615d1a556e39a00d386b7c63087697c03d97e0561033d",
    ),
    "terabox-gateway-main.zip": (
        "terabox-gateway-main",
        "646e621836e40c6e21cbb510d1c69ce278cea3ef77e7dc72a320a8701b38c394",
    ),
}


def check_entries(archive: ZipFile, top_level: str) -> None:
    entries = archive.infolist()
    if len(entries) > 1000 or sum(info.file_size for info in entries) > 100 * 1024 * 1024:
        raise ValueError("Reference archive exceeds extraction limits")
    seen = set()
    for info in entries:
        path = PurePosixPath(info.filename)
        raw_parts = info.filename.rstrip("/").split("/")
        mode = info.external_attr >> 16
        if (
            not info.filename
            or "\\" in info.filename
            or path.is_absolute()
            or path.parts[0] != top_level
            or any(part in ("", ".", "..") for part in raw_parts)
            or info.filename in seen
            or stat.S_ISLNK(mode)
            or (mode and not (stat.S_ISREG(mode) or stat.S_ISDIR(mode)))
        ):
            raise ValueError(f"Unsafe archive member: {info.filename}")
        seen.add(info.filename)
    if archive.testzip() is not None:
        raise ValueError("Reference archive failed CRC validation")


def verify_existing(archive: ZipFile, destination: Path, top_level: str) -> None:
    for info in archive.infolist():
        relative = PurePosixPath(info.filename).relative_to(top_level)
        target = destination.joinpath(*relative.parts)
        if target.is_symlink() or (info.is_dir() and not target.is_dir()):
            raise ValueError(f"Existing extraction differs: {target}")
        if not info.is_dir():
            if not target.is_file() or sha256(target.read_bytes()).digest() != sha256(archive.read(info)).digest():
                raise ValueError(f"Existing extraction differs: {target}")


def main() -> None:
    if OUTPUT.is_symlink():
        raise ValueError("Reference output directory must not be a symlink")
    OUTPUT.mkdir(exist_ok=True)
    for filename, (top_level, expected_hash) in ARCHIVES.items():
        source = ARCHIVE_DIR / filename
        if sha256(source.read_bytes()).hexdigest() != expected_hash:
            raise ValueError(f"Archive checksum differs: {filename}")
        with ZipFile(source) as archive:
            check_entries(archive, top_level)
            destination = OUTPUT / top_level
            if destination.exists() or destination.is_symlink():
                if destination.is_symlink() or not destination.is_dir():
                    raise ValueError(f"Existing extraction differs: {destination}")
                verify_existing(archive, destination, top_level)
            else:
                with tempfile.TemporaryDirectory(dir=OUTPUT) as temporary:
                    archive.extractall(temporary)
                    shutil.move(str(Path(temporary) / top_level), destination)
            print(f"Verified {filename} -> {destination.relative_to(ROOT)}")


if __name__ == "__main__":
    main()
