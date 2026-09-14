from __future__ import annotations

import hashlib
import platform
import shutil
import tempfile
import urllib.request
from pathlib import Path


PANDOC_VERSION = "3.11"
PROJECT_ROOT = Path(__file__).resolve().parents[1]
INSTALL_DIR = PROJECT_ROOT / ".tools" / "pandoc" / PANDOC_VERSION
PANDOC_PATH = INSTALL_DIR / "pandoc"

ARTIFACTS = {
    ("Darwin", "arm64"): (
        f"pandoc-{PANDOC_VERSION}-arm64-macOS.zip",
        "15806bedf9517bfead72e88fe6a6696635c3691efbb6e152173440e9c5bb50b4",
    ),
    ("Darwin", "x86_64"): (
        f"pandoc-{PANDOC_VERSION}-x86_64-macOS.zip",
        "3b1c1b57f160112c821d02f23d946ede8b7f57a6ccf4632a25a512d334a9291f",
    ),
    ("Linux", "aarch64"): (
        f"pandoc-{PANDOC_VERSION}-linux-arm64.tar.gz",
        "56ed5566ec41d22ec9ee0704e6ac0b98ba102e92384efd5306173a22d314c79a",
    ),
    ("Linux", "x86_64"): (
        f"pandoc-{PANDOC_VERSION}-linux-amd64.tar.gz",
        "37edb3bbcf722f921a009941bf5874e2e0c09263226c9b4a2d980788cb062ab6",
    ),
}


def sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as file:
        for chunk in iter(lambda: file.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def main() -> None:
    if PANDOC_PATH.is_file():
        print(f"Pandoc {PANDOC_VERSION} is already installed at {PANDOC_PATH}")
        return

    platform_key = (platform.system(), platform.machine())
    if platform_key not in ARTIFACTS:
        raise RuntimeError(f"Unsupported Pandoc platform: {platform_key}")

    artifact, expected_sha256 = ARTIFACTS[platform_key]
    url = f"https://github.com/jgm/pandoc/releases/download/{PANDOC_VERSION}/{artifact}"

    with tempfile.TemporaryDirectory() as temporary_directory:
        temporary_path = Path(temporary_directory)
        archive_path = temporary_path / artifact
        extract_path = temporary_path / "extracted"
        print(f"Downloading Pandoc {PANDOC_VERSION} for {platform_key[0]} {platform_key[1]}...")
        urllib.request.urlretrieve(url, archive_path)

        actual_sha256 = sha256(archive_path)
        if actual_sha256 != expected_sha256:
            raise RuntimeError(
                f"Pandoc checksum mismatch: expected {expected_sha256}, got {actual_sha256}"
            )

        shutil.unpack_archive(archive_path, extract_path)
        candidates = [
            path
            for path in extract_path.rglob("pandoc")
            if path.is_file() and path.parent.name == "bin"
        ]
        if len(candidates) != 1:
            raise RuntimeError(f"Expected one Pandoc executable, found {len(candidates)}")

        INSTALL_DIR.mkdir(parents=True, exist_ok=True)
        shutil.copy2(candidates[0], PANDOC_PATH)
        PANDOC_PATH.chmod(0o755)

    print(f"Installed Pandoc {PANDOC_VERSION} at {PANDOC_PATH}")


if __name__ == "__main__":
    main()
