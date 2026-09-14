from __future__ import annotations

import hashlib
import platform
import shutil
import tempfile
import urllib.request
from pathlib import Path


TYPST_VERSION = "0.15.1"
PROJECT_ROOT = Path(__file__).resolve().parents[1]
INSTALL_DIR = PROJECT_ROOT / ".tools" / "typst" / TYPST_VERSION
TYPST_PATH = INSTALL_DIR / "typst"

ARTIFACTS = {
    ("Darwin", "arm64"): (
        "typst-aarch64-apple-darwin.tar.xz",
        "48f62ed034aa3a7978309579ac6ca00045e2ef0da73114e8af27cfd8e74dc05a",
    ),
    ("Darwin", "x86_64"): (
        "typst-x86_64-apple-darwin.tar.xz",
        "7f9fdd9584866245de9a79e0add8f9236fae6f40a8a45e2c4771ccc14db4e0fa",
    ),
    ("Linux", "aarch64"): (
        "typst-aarch64-unknown-linux-musl.tar.xz",
        "5aa8d74a3d906e60ea12a66ac2f37f8eef1b14cbad7182a745e393a10c23dcee",
    ),
    ("Linux", "x86_64"): (
        "typst-x86_64-unknown-linux-musl.tar.xz",
        "a6d077d0a95eed5a2eba715b2dae06be954f624ccbf85758a03f389ded33118c",
    ),
}


def sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as file:
        for chunk in iter(lambda: file.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def main() -> None:
    if TYPST_PATH.is_file():
        print(f"Typst {TYPST_VERSION} is already installed at {TYPST_PATH}")
        return

    platform_key = (platform.system(), platform.machine())
    if platform_key not in ARTIFACTS:
        raise RuntimeError(f"Unsupported Typst platform: {platform_key}")

    artifact, expected_sha256 = ARTIFACTS[platform_key]
    url = (
        f"https://github.com/typst/typst/releases/download/"
        f"v{TYPST_VERSION}/{artifact}"
    )

    with tempfile.TemporaryDirectory() as temporary_directory:
        temporary_path = Path(temporary_directory)
        archive_path = temporary_path / artifact
        extract_path = temporary_path / "extracted"
        print(f"Downloading Typst {TYPST_VERSION} for {platform_key[0]} {platform_key[1]}...")
        urllib.request.urlretrieve(url, archive_path)

        actual_sha256 = sha256(archive_path)
        if actual_sha256 != expected_sha256:
            raise RuntimeError(
                f"Typst checksum mismatch: expected {expected_sha256}, got {actual_sha256}"
            )

        shutil.unpack_archive(archive_path, extract_path)
        candidates = [
            path
            for path in extract_path.rglob("typst")
            if path.is_file() and path.name == "typst"
        ]
        if len(candidates) != 1:
            raise RuntimeError(f"Expected one Typst executable, found {len(candidates)}")

        INSTALL_DIR.mkdir(parents=True, exist_ok=True)
        shutil.copy2(candidates[0], TYPST_PATH)
        TYPST_PATH.chmod(0o755)

    print(f"Installed Typst {TYPST_VERSION} at {TYPST_PATH}")


if __name__ == "__main__":
    main()
