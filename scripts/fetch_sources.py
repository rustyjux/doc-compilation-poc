from __future__ import annotations

import hashlib
import shutil
import subprocess
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

import yaml


PROJECT_ROOT = Path(__file__).resolve().parents[1]
WORK_DIR = PROJECT_ROOT / ".work"
INPUT_DIR = WORK_DIR / "inputs"
REPO_DIR = WORK_DIR / "repos"
CONFIG_PATH = PROJECT_ROOT / "sources.yaml"
LOCK_PATH = PROJECT_ROOT / "sources.lock.yaml"


def file_sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as source_file:
        for chunk in iter(lambda: source_file.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def combined_sha256(files: list[dict[str, Any]]) -> str:
    digest = hashlib.sha256()
    for file in files:
        digest.update(file["path"].encode())
        digest.update(b"\0")
        digest.update(file["sha256"].encode())
        digest.update(b"\n")
    return digest.hexdigest()


def run_git(*args: str, cwd: Path | None = None) -> str:
    result = subprocess.run(
        ["git", *args],
        cwd=cwd,
        capture_output=True,
        text=True,
    )
    if result.returncode != 0:
        detail = result.stderr.strip() or result.stdout.strip()
        raise RuntimeError(f"git {' '.join(args)} failed: {detail}")
    return result.stdout.strip()


def copy_and_describe(source: Path, destination: Path, display_path: str) -> dict[str, Any]:
    destination.parent.mkdir(parents=True, exist_ok=True)
    shutil.copy2(source, destination)
    return {
        "path": display_path,
        "sha256": file_sha256(destination),
        "size_bytes": destination.stat().st_size,
    }


def flatten_navigation(value: Any) -> list[str]:
    if isinstance(value, str):
        return [value]
    if isinstance(value, list):
        return [path for item in value for path in flatten_navigation(item)]
    if isinstance(value, dict):
        return [path for item in value.values() for path in flatten_navigation(item)]
    return []


def fetch_local(source: dict[str, Any]) -> dict[str, Any]:
    location = PROJECT_ROOT / source["location"]
    if not location.is_file():
        raise FileNotFoundError(f"Local source does not exist: {source['location']}")

    destination = INPUT_DIR / source["id"] / location.name
    file = copy_and_describe(location, destination, location.name)
    return {
        "id": source["id"],
        "title": source["title"],
        "type": source["type"],
        "location": source["location"],
        "order": source["order"],
        "content_sha256": combined_sha256([file]),
        "files": [file],
    }


def fetch_git(source: dict[str, Any]) -> dict[str, Any]:
    checkout = REPO_DIR / source["id"]
    run_git(
        "clone",
        "--depth",
        "1",
        "--filter=blob:none",
        "--single-branch",
        "--branch",
        source["ref"],
        source["repository"],
        str(checkout),
    )
    revision = run_git("rev-parse", "HEAD", cwd=checkout)

    source_root = (checkout / source.get("root", ".")).resolve()
    if not source_root.is_relative_to(checkout.resolve()) or not source_root.is_dir():
        raise ValueError(f"Invalid source root for {source['id']}: {source.get('root', '.')}")

    selected: dict[Path, None] = {}
    for pattern in source["include"]:
        for path in source_root.glob(pattern):
            if path.is_file():
                selected[path] = None

    if not selected:
        raise ValueError(f"No files matched the include rules for {source['id']}")

    files = []
    for path in sorted(selected):
        relative_path = path.relative_to(source_root)
        destination = INPUT_DIR / source["id"] / relative_path
        files.append(copy_and_describe(path, destination, relative_path.as_posix()))

    locked_source = {
        "id": source["id"],
        "title": source["title"],
        "type": source["type"],
        "repository": source["repository"],
        "ref": source["ref"],
        "revision": revision,
        "root": source.get("root", "."),
        "order": source["order"],
        "content_sha256": combined_sha256(files),
        "files": files,
    }

    if navigation_path := source.get("navigation"):
        navigation_file = source_root / navigation_path
        if not navigation_file.is_file():
            raise FileNotFoundError(
                f"Navigation file does not exist for {source['id']}: {navigation_path}"
            )
        with navigation_file.open() as nav_file:
            navigation = yaml.safe_load(nav_file)

        docs_dir = Path(navigation.get("docs_dir", "docs"))
        selected_paths = {file["path"] for file in files}
        nav_paths = [
            (docs_dir / path).as_posix()
            for path in flatten_navigation(navigation.get("nav", []))
        ]
        document_order = [path for path in nav_paths if path in selected_paths]
        unlisted = sorted(selected_paths - set(document_order))
        locked_source["navigation"] = {
            "path": navigation_path,
            "sha256": file_sha256(navigation_file),
            "docs_dir": docs_dir.as_posix(),
            "unlisted_files": unlisted,
        }
        locked_source["document_order"] = [*document_order, *unlisted]

    if component := source.get("techdocs_component"):
        locked_source["techdocs_component"] = component

    return locked_source


def load_sources() -> dict[str, Any]:
    with CONFIG_PATH.open() as config_file:
        config = yaml.safe_load(config_file)

    sources = config.get("sources", [])
    ids = [source["id"] for source in sources]
    orders = [source["order"] for source in sources]
    if len(ids) != len(set(ids)):
        raise ValueError("Source IDs must be unique")
    if len(orders) != len(set(orders)):
        raise ValueError("Source order values must be unique")
    return config


def main() -> None:
    config = load_sources()
    shutil.rmtree(WORK_DIR, ignore_errors=True)
    INPUT_DIR.mkdir(parents=True)
    REPO_DIR.mkdir(parents=True)

    locked_sources = []
    for source in sorted(config["sources"], key=lambda item: item["order"]):
        print(f"Fetching {source['id']}...")
        match source["type"]:
            case "docx":
                locked_sources.append(fetch_local(source))
            case "git":
                locked_sources.append(fetch_git(source))
            case unsupported:
                raise ValueError(f"Unsupported source type: {unsupported}")

    lock = {
        "schema_version": config["schema_version"],
        "generated_at": datetime.now(UTC).isoformat(),
        "sources": locked_sources,
    }
    LOCK_PATH.write_text(yaml.safe_dump(lock, sort_keys=False), encoding="utf-8")
    print(f"Fetched {len(locked_sources)} sources into {INPUT_DIR.relative_to(PROJECT_ROOT)}")
    print(f"Wrote {LOCK_PATH.name}")


if __name__ == "__main__":
    main()
