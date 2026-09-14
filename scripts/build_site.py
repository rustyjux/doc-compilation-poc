from __future__ import annotations

import re
import shutil
import subprocess
import sys
from pathlib import Path
from typing import Any

import yaml


from expand_tabs import mark_external_links


PROJECT_ROOT = Path(__file__).resolve().parents[1]
DIST_DIR = PROJECT_ROOT / "dist"
PAGE_DIR = PROJECT_ROOT / ".work" / "pages"
SITE_DIR = PROJECT_ROOT / "site"
SOURCE_LOCK_PATH = PROJECT_ROOT / "sources.lock.yaml"
NORMALIZED_MANIFEST_PATH = PROJECT_ROOT / ".work" / "normalized" / "manifest.yaml"
HEADING_PATTERN = re.compile(r"^(#{1,6})(\s+.+)$")
SOURCE_HEADING_PATTERN = re.compile(r"^#\s+.+\{#source-[^}]+\}\s*$")


def prepare_page(markdown: str) -> str:
    lines = markdown.splitlines()
    if not lines or not lines[0].startswith("# "):
        raise ValueError("Expected the master document to start with an H1")
    lines[1:1] = [
        "",
        "[Download PDF](master.pdf){ .md-button .md-button--primary }",
    ]

    inside_source = False
    in_fence = False
    for index, line in enumerate(lines):
        stripped = line.lstrip()
        if stripped.startswith(("```", "~~~")):
            in_fence = not in_fence
            continue
        if in_fence:
            continue
        if SOURCE_HEADING_PATTERN.match(line):
            inside_source = True
        if inside_source and (heading := HEADING_PATTERN.match(line)):
            level = len(heading.group(1))
            lines[index] = f"{'#' * min(level + 1, 6)}{heading.group(2)}"

    return mark_external_links("\n".join(lines) + "\n", "assets/external-link.svg")


def _short_sha(value: str, length: int = 12) -> str:
    return value if len(value) <= length else f"{value[:length]}…"


def render_manifest_page(
    source_lock: dict[str, Any],
    normalized_manifest: dict[str, Any] | None,
) -> str:
    normalized_by_id = {
        source["id"]: source
        for source in (normalized_manifest or {}).get("sources", [])
    }
    lines = [
        "# Source manifest",
        "",
        "Provenance captured for this generated build.",
        "",
        f"- Lock generated at: `{source_lock.get('generated_at', 'unknown')}`",
        f"- Schema version: `{source_lock.get('schema_version', 'unknown')}`",
        f"- Sources: `{len(source_lock.get('sources', []))}`",
        "",
    ]

    for source in sorted(source_lock.get("sources", []), key=lambda item: item["order"]):
        lines.extend(
            [
                f"## {source.get('title', source['id'])}",
                "",
                f"- ID: `{source['id']}`",
                f"- Type: `{source['type']}`",
                f"- Order: `{source['order']}`",
                f"- Content SHA-256: `{source['content_sha256']}`",
            ]
        )
        if source["type"] == "git":
            revision = source["revision"]
            repo = source["repository"].removesuffix(".git")
            lines.extend(
                [
                    f"- Repository: [{source['repository']}]({source['repository']})",
                    f"- Ref: `{source['ref']}`",
                    f"- Revision: [`{_short_sha(revision, 12)}`]({repo}/commit/{revision})",
                    f"- Root: `{source.get('root', '.')}`",
                ]
            )
            if component := source.get("techdocs_component"):
                lines.append(f"- TechDocs component: `{component}`")
        else:
            lines.append(f"- Location: `{source['location']}`")

        navigation = source.get("navigation", {})
        if navigation:
            unlisted = navigation.get("unlisted_files", [])
            lines.append(f"- Navigation: `{navigation.get('path', 'mkdocs.yml')}`")
            if unlisted:
                lines.append("- Files absent from source navigation (appended last):")
                lines.extend(f"  - `{path}`" for path in unlisted)
            else:
                lines.append("- All selected files appear in source navigation.")

        document_order = source.get("document_order")
        if not document_order and source["id"] in normalized_by_id:
            document_order = [
                document["source_path"]
                for document in sorted(
                    normalized_by_id[source["id"]]["documents"],
                    key=lambda item: item["position"],
                )
            ]
        if not document_order:
            document_order = [file["path"] for file in source.get("files", [])]

        lines.extend(["", "### Included files", ""])
        for position, path in enumerate(document_order, start=1):
            file_meta = next(
                (file for file in source.get("files", []) if file["path"] == path),
                None,
            )
            if file_meta:
                lines.append(
                    f"{position}. `{path}` — `{_short_sha(file_meta['sha256'])}` "
                    f"({file_meta['size_bytes']} bytes)"
                )
            else:
                lines.append(f"{position}. `{path}`")
        lines.append("")

    return "\n".join(lines).rstrip() + "\n"


def main() -> None:
    master_path = DIST_DIR / "master.md"
    pdf_path = DIST_DIR / "master.pdf"
    report_path = DIST_DIR / "validation-report.md"
    for required_path in (master_path, pdf_path, report_path, SOURCE_LOCK_PATH):
        if not required_path.is_file():
            raise FileNotFoundError(f"Required publication file does not exist: {required_path}")

    with SOURCE_LOCK_PATH.open() as lock_file:
        source_lock = yaml.safe_load(lock_file)

    normalized_manifest = None
    if NORMALIZED_MANIFEST_PATH.is_file():
        with NORMALIZED_MANIFEST_PATH.open() as manifest_file:
            normalized_manifest = yaml.safe_load(manifest_file)

    shutil.rmtree(PAGE_DIR, ignore_errors=True)
    PAGE_DIR.mkdir(parents=True)
    (PAGE_DIR / "index.md").write_text(
        prepare_page(master_path.read_text(encoding="utf-8")),
        encoding="utf-8",
    )
    (PAGE_DIR / "manifest.md").write_text(
        mark_external_links(
            render_manifest_page(source_lock, normalized_manifest),
            "assets/external-link.svg",
        ),
        encoding="utf-8",
    )
    shutil.copy2(pdf_path, PAGE_DIR / pdf_path.name)
    shutil.copy2(report_path, PAGE_DIR / report_path.name)

    stylesheet_source = PROJECT_ROOT / "stylesheets" / "extra.css"
    stylesheet_destination = PAGE_DIR / "stylesheets" / "extra.css"
    stylesheet_destination.parent.mkdir(parents=True, exist_ok=True)
    shutil.copy2(stylesheet_source, stylesheet_destination)

    icon_source = PROJECT_ROOT / "templates" / "external-link.svg"
    page_assets = PAGE_DIR / "assets"
    page_assets.mkdir(parents=True, exist_ok=True)
    shutil.copy2(icon_source, page_assets / icon_source.name)

    asset_dir = DIST_DIR / "assets"
    if asset_dir.is_dir():
        shutil.copytree(asset_dir, PAGE_DIR / "assets", dirs_exist_ok=True)

    result = subprocess.run(
        [sys.executable, "-m", "mkdocs", "build", "--strict"],
        cwd=PROJECT_ROOT,
        capture_output=True,
        text=True,
    )
    if result.returncode != 0:
        detail = result.stderr.strip() or result.stdout.strip()
        raise RuntimeError(f"Site build failed: {detail}")

    print(f"Wrote GitHub Pages site to {SITE_DIR.relative_to(PROJECT_ROOT)}")


if __name__ == "__main__":
    main()
