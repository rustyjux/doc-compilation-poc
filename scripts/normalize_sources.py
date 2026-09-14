from __future__ import annotations

import hashlib
import os
import shutil
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

from install_pandoc import PANDOC_PATH

os.environ["PYPANDOC_PANDOC"] = str(PANDOC_PATH)

import pypandoc
import yaml


PROJECT_ROOT = Path(__file__).resolve().parents[1]
WORK_DIR = PROJECT_ROOT / ".work"
INPUT_DIR = WORK_DIR / "inputs"
OUTPUT_DIR = WORK_DIR / "normalized"
SOURCE_LOCK_PATH = PROJECT_ROOT / "sources.lock.yaml"
MANIFEST_PATH = OUTPUT_DIR / "manifest.yaml"


def file_sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as source_file:
        for chunk in iter(lambda: source_file.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def describe_file(path: Path, base: Path) -> dict[str, Any]:
    return {
        "path": path.relative_to(base).as_posix(),
        "sha256": file_sha256(path),
        "size_bytes": path.stat().st_size,
    }


def normalize_markdown(source: dict[str, Any], output: Path) -> list[dict[str, Any]]:
    input_root = INPUT_DIR / source["id"]
    file_paths = {file["path"] for file in source["files"]}
    ordered_paths = source.get("document_order", sorted(file_paths))
    if set(ordered_paths) != file_paths:
        raise ValueError(f"Document order does not match selected files for {source['id']}")

    documents = []
    for position, relative_path in enumerate(ordered_paths, start=1):
        source_path = input_root / relative_path
        destination = output / relative_path
        destination.parent.mkdir(parents=True, exist_ok=True)
        shutil.copy2(source_path, destination)
        documents.append(
            {
                "position": position,
                "source_path": relative_path,
                **describe_file(destination, output),
            }
        )

    for asset in source.get("assets", []):
        source_path = input_root / asset["path"]
        destination = output / asset["path"]
        destination.parent.mkdir(parents=True, exist_ok=True)
        shutil.copy2(source_path, destination)

    return documents


def normalize_docx(source: dict[str, Any], output: Path) -> list[dict[str, Any]]:
    input_path = INPUT_DIR / source["id"] / source["files"][0]["path"]
    output_path = output / f"{input_path.stem}.md"
    output.mkdir(parents=True, exist_ok=True)

    pypandoc.convert_file(
        str(input_path),
        to="gfm",
        outputfile=str(output_path),
        extra_args=[
            "--wrap=none",
            f"--extract-media={output}",
        ],
    )
    return [
        {
            "position": 1,
            "source_path": source["files"][0]["path"],
            **describe_file(output_path, output),
        }
    ]


def main() -> None:
    if not SOURCE_LOCK_PATH.is_file():
        raise FileNotFoundError("Run fetch_sources.py before normalizing sources")
    if not PANDOC_PATH.is_file():
        raise FileNotFoundError("Run install_pandoc.py before normalizing sources")

    with SOURCE_LOCK_PATH.open() as lock_file:
        source_lock = yaml.safe_load(lock_file)

    shutil.rmtree(OUTPUT_DIR, ignore_errors=True)
    OUTPUT_DIR.mkdir(parents=True)

    normalized_sources = []
    for source in sorted(source_lock["sources"], key=lambda item: item["order"]):
        print(f"Normalizing {source['id']}...")
        source_output = OUTPUT_DIR / source["id"]
        match source["type"]:
            case "git":
                documents = normalize_markdown(source, source_output)
            case "docx":
                documents = normalize_docx(source, source_output)
            case unsupported:
                raise ValueError(f"Unsupported source type: {unsupported}")

        document_paths = {document["path"] for document in documents}
        assets = [
            describe_file(path, source_output)
            for path in sorted(source_output.rglob("*"))
            if path.is_file() and path.relative_to(source_output).as_posix() not in document_paths
        ]
        normalized_sources.append(
            {
                "id": source["id"],
                "type": source["type"],
                "order": source["order"],
                "source_content_sha256": source["content_sha256"],
                "documents": documents,
                "assets": assets,
            }
        )

    manifest = {
        "schema_version": source_lock["schema_version"],
        "generated_at": datetime.now(UTC).isoformat(),
        "sources": normalized_sources,
    }
    MANIFEST_PATH.write_text(
        yaml.safe_dump(manifest, sort_keys=False),
        encoding="utf-8",
    )
    document_count = sum(len(source["documents"]) for source in normalized_sources)
    asset_count = sum(len(source["assets"]) for source in normalized_sources)
    print(f"Normalized {document_count} documents and extracted {asset_count} assets")
    print(f"Wrote {MANIFEST_PATH.relative_to(PROJECT_ROOT)}")


if __name__ == "__main__":
    main()
