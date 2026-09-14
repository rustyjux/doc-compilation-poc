from __future__ import annotations

import posixpath
import re
import shutil
import unicodedata
from pathlib import Path
from typing import Any
from urllib.parse import unquote

import yaml


PROJECT_ROOT = Path(__file__).resolve().parents[1]
NORMALIZED_DIR = PROJECT_ROOT / ".work" / "normalized"
MANIFEST_PATH = NORMALIZED_DIR / "manifest.yaml"
SOURCE_LOCK_PATH = PROJECT_ROOT / "sources.lock.yaml"
OUTPUT_DIR = PROJECT_ROOT / "dist"
MASTER_PATH = OUTPUT_DIR / "master.md"
REPORT_PATH = OUTPUT_DIR / "validation-report.md"

HEADING_PATTERN = re.compile(r"^(#{1,6})\s+(.+?)\s*$")
LINK_PATTERN = re.compile(
    r"(?P<image>!?)\[(?P<label>[^\]]*)\]\("
    r"(?P<target><[^>]+>|[^)\s]+)(?P<suffix>[^)]*)\)"
)
TECHDOCS_PATTERN = re.compile(r"^/docs/default/component/([^/]+)/(.+?)/?$")
LEGACY_ANCHOR_PATTERN = re.compile(
    r"""^\s*<a\s+(?:name|id)=["'][^"']+["']\s*></a>\s*$""",
    re.IGNORECASE,
)


def slugify(value: str) -> str:
    value = unquote(value).strip().lower()
    value = unicodedata.normalize("NFKD", value)
    value = "".join(character for character in value if not unicodedata.combining(character))
    value = re.sub(r"<[^>]+>", "", value)
    value = re.sub(r"\[([^\]]+)\]\([^)]+\)", r"\1", value)
    value = value.replace("_", "-")
    value = re.sub(r"[^\w\s-]", "", value)
    value = re.sub(r"[-\s]+", "-", value)
    return value.strip("-") or "section"


def clean_heading(value: str) -> str:
    value = re.sub(r"\s+\{[^}]+\}\s*$", "", value)
    value = re.sub(r"\s+#+\s*$", "", value)
    value = re.sub(r"\[([^\]]+)\]\([^)]+\)", r"\1", value)
    value = re.sub(r"[*_`]", "", value)
    return re.sub(r"<[^>]+>", "", value).strip()


def split_frontmatter(text: str) -> tuple[dict[str, Any], list[str]]:
    lines = text.splitlines()
    if not lines or lines[0].strip() != "---":
        return {}, lines
    try:
        end = next(index for index, line in enumerate(lines[1:], start=1) if line.strip() == "---")
    except StopIteration:
        return {}, lines
    metadata = yaml.safe_load("\n".join(lines[1:end])) or {}
    return metadata, lines[end + 1 :]


def prepare_document(
    source: dict[str, Any],
    document: dict[str, Any],
) -> dict[str, Any]:
    path = NORMALIZED_DIR / source["id"] / document["path"]
    metadata, lines = split_frontmatter(path.read_text(encoding="utf-8"))
    document_anchor = slugify(f"{source['id']}--{document['path'].removesuffix('.md')}")

    raw_headings = []
    in_fence = False
    for line_number, line in enumerate(lines):
        stripped = line.lstrip()
        if stripped.startswith(("```", "~~~")):
            in_fence = not in_fence
            continue
        if in_fence or not (match := HEADING_PATTERN.match(line)):
            continue

        title = clean_heading(match.group(2))
        raw_headings.append(
            {
                "line_number": line_number,
                "level": len(match.group(1)),
                "title": title,
            }
        )

    title = str(
        metadata.get("title")
        or (raw_headings[0]["title"] if raw_headings else Path(document["path"]).stem)
    )
    skipped_lines = set()
    if metadata.get("title"):
        title_heading = next(
            (
                heading
                for heading in raw_headings
                if slugify(heading["title"]) == slugify(title)
            ),
            None,
        )
        if title_heading:
            skipped_lines.add(title_heading["line_number"])
            skipped_lines.update(
                heading["line_number"]
                for heading in raw_headings
                if heading["line_number"] < title_heading["line_number"]
                and heading["level"] == 1
            )
    elif raw_headings:
        skipped_lines.add(raw_headings[0]["line_number"])

    headings = {}
    fragment_map = {}
    heading_counts: dict[str, int] = {}
    for heading in raw_headings:
        line_number = heading["line_number"]
        heading_title = heading["title"]
        base_slug = slugify(heading_title)
        if line_number in skipped_lines:
            headings[line_number] = {**heading, "skip": True}
            fragment_map.setdefault(base_slug, document_anchor)
            continue

        base_slug = slugify(heading_title)
        count = heading_counts.get(base_slug, 0)
        heading_counts[base_slug] = count + 1
        unique_slug = base_slug if count == 0 else f"{base_slug}-{count}"
        output_level = (
            max(3, heading["level"])
            if metadata.get("title")
            else heading["level"] + 1
        )
        anchor = f"{document_anchor}--{unique_slug}"
        headings[line_number] = {
            **heading,
            "anchor": anchor,
            "output_level": min(output_level, 6),
            "capped": output_level > 6,
            "skip": False,
        }
        fragment_map.setdefault(base_slug, anchor)

    return {
        **document,
        "source_id": source["id"],
        "source": source,
        "title": title,
        "anchor": document_anchor,
        "lines": lines,
        "headings": headings,
        "fragment_map": fragment_map,
    }


def path_aliases(document: dict[str, Any]) -> set[str]:
    path = document["path"].lstrip("/")
    aliases = {path}
    docs_dir = document["source"].get("navigation", {}).get("docs_dir")
    if docs_dir and path.startswith(f"{docs_dir}/"):
        aliases.add(path.removeprefix(f"{docs_dir}/"))

    for alias in list(aliases):
        if alias.endswith(".md"):
            aliases.add(alias.removesuffix(".md"))
        if alias.endswith("/index.md"):
            aliases.add(alias.removesuffix("index.md").rstrip("/"))
    return aliases


def is_section_heading(heading: dict[str, Any]) -> bool:
    """Identify likely document sections vs body text wrongly styled as H1."""
    if heading.get("skip") or heading["level"] != 1:
        return False
    title = heading["title"].strip()
    if title.endswith((".", "!")):
        return False
    return len(title.split()) <= 8


def toc_entries_for_source(
    source_documents: list[dict[str, Any]],
) -> list[dict[str, str]]:
    if len(source_documents) != 1:
        return [
            {"title": document["title"], "anchor": document["anchor"]}
            for document in source_documents
        ]

    document = source_documents[0]
    entries = [{"title": document["title"], "anchor": document["anchor"]}]
    for heading in sorted(
        document["headings"].values(),
        key=lambda item: item["line_number"],
    ):
        if not is_section_heading(heading):
            continue
        entries.append({"title": heading["title"], "anchor": heading["anchor"]})
    return entries


def resolve_document(
    current: dict[str, Any],
    target_path: str,
    documents_by_alias: dict[tuple[str, str], dict[str, Any]],
    sources_by_component: dict[str, dict[str, Any]],
) -> dict[str, Any] | None:
    techdocs_match = TECHDOCS_PATTERN.match(target_path)
    if techdocs_match:
        component, component_path = techdocs_match.groups()
        target_source = sources_by_component.get(component)
        if not target_source:
            return None
        return documents_by_alias.get((target_source["id"], component_path.rstrip("/")))

    if target_path.startswith("/"):
        normalized = posixpath.normpath(target_path.lstrip("/"))
    else:
        normalized = posixpath.normpath(
            posixpath.join(posixpath.dirname(current["path"]), target_path)
        )

    source_id = current["source_id"]
    candidates = [normalized]
    if normalized.endswith(".md"):
        candidates.append(normalized.removesuffix(".md"))
    else:
        candidates.append(f"{normalized}.md")
    return next(
        (
            documents_by_alias[(source_id, candidate)]
            for candidate in candidates
            if (source_id, candidate) in documents_by_alias
        ),
        None,
    )


def rewrite_target(
    current: dict[str, Any],
    target: str,
    documents_by_alias: dict[tuple[str, str], dict[str, Any]],
    sources_by_component: dict[str, dict[str, Any]],
    assets_by_alias: dict[tuple[str, str], str],
    validation: dict[str, Any],
) -> str:
    wrapped = target.startswith("<") and target.endswith(">")
    raw_target = target[1:-1] if wrapped else target

    if re.match(r"^[a-zA-Z][a-zA-Z0-9+.-]*:", raw_target) or raw_target.startswith("//"):
        validation["external_links"] += 1
        return target

    target_without_fragment, separator, fragment = raw_target.partition("#")
    target_path = target_without_fragment.split("?", maxsplit=1)[0]

    if not target_path:
        target_document = current
    else:
        target_document = resolve_document(
            current,
            target_path,
            documents_by_alias,
            sources_by_component,
        )

    if target_document:
        anchor = target_document["anchor"]
        if separator and fragment:
            fragment_anchor = target_document["fragment_map"].get(slugify(fragment))
            if fragment_anchor:
                anchor = fragment_anchor
            else:
                validation["unresolved"].append(
                    {
                        "source": f"{current['source_id']}:{current['path']}",
                        "target": raw_target,
                        "reason": "heading fragment was not found; linked to the target document",
                    }
                )
        validation["rewritten_links"] += 1
        return f"#{anchor}"

    if target_path:
        normalized_asset = (
            posixpath.normpath(target_path.lstrip("/"))
            if target_path.startswith("/")
            else posixpath.normpath(
                posixpath.join(posixpath.dirname(current["path"]), target_path)
            )
        )
        asset = assets_by_alias.get((current["source_id"], normalized_asset))
        if asset:
            validation["rewritten_links"] += 1
            return asset

    if raw_target.startswith("/catalogue"):
        validation["site_relative_links"] += 1
        return f"https://developer.gov.bc.ca{raw_target}"

    validation["unresolved"].append(
        {
            "source": f"{current['source_id']}:{current['path']}",
            "target": raw_target,
            "reason": "target is outside the selected source files",
        }
    )
    if raw_target.startswith("/docs/default/"):
        return public_techdocs_url(raw_target)
    component = current["source"].get("techdocs_component")
    if component and raw_target.startswith("/"):
        return public_techdocs_url(raw_target, component)
    return target


def public_techdocs_url(path: str, component: str | None = None) -> str:
    """Build a public DevHub URL; drop .md so the link works outside MkDocs."""
    path_part, _, fragment = path.partition("#")
    path_part, _, query = path_part.partition("?")
    if path_part.endswith(".md"):
        path_part = path_part[: -len(".md")]
    if component:
        url = (
            "https://developer.gov.bc.ca/docs/default/component/"
            f"{component}{path_part}"
        )
    else:
        url = f"https://developer.gov.bc.ca{path_part}"
    if query:
        url += f"?{query}"
    if fragment:
        url += f"#{fragment}"
    return url


def rewrite_line(
    line: str,
    current: dict[str, Any],
    documents_by_alias: dict[tuple[str, str], dict[str, Any]],
    sources_by_component: dict[str, dict[str, Any]],
    assets_by_alias: dict[tuple[str, str], str],
    validation: dict[str, Any],
) -> str:
    def replace(match: re.Match[str]) -> str:
        rewritten_target = rewrite_target(
            current,
            match.group("target"),
            documents_by_alias,
            sources_by_component,
            assets_by_alias,
            validation,
        )
        return (
            f"{match.group('image')}[{match.group('label')}]"
            f"({rewritten_target}{match.group('suffix')})"
        )

    return LINK_PATTERN.sub(replace, line)


def provenance(source: dict[str, Any], document: dict[str, Any]) -> str:
    if source["type"] == "git":
        return (
            f"{source['repository']}@{source['revision']}:"
            f"{source.get('root', '.')}/{document['source_path']}"
        )
    return source["location"]


def main() -> None:
    if not MANIFEST_PATH.is_file():
        raise FileNotFoundError("Run normalize_sources.py before assembling the master document")

    with MANIFEST_PATH.open() as manifest_file:
        manifest = yaml.safe_load(manifest_file)
    with SOURCE_LOCK_PATH.open() as source_lock_file:
        source_lock = yaml.safe_load(source_lock_file)

    locked_sources = {source["id"]: source for source in source_lock["sources"]}
    prepared_sources = []
    documents = []
    for normalized_source in sorted(manifest["sources"], key=lambda item: item["order"]):
        source = locked_sources[normalized_source["id"]]
        prepared_documents = [
            prepare_document(source, document)
            for document in sorted(
                normalized_source["documents"],
                key=lambda item: item["position"],
            )
        ]
        prepared_sources.append((source, normalized_source, prepared_documents))
        documents.extend(prepared_documents)

    documents_by_alias = {
        (document["source_id"], alias): document
        for document in documents
        for alias in path_aliases(document)
    }
    sources_by_component = {
        source["techdocs_component"]: source
        for source in locked_sources.values()
        if source.get("techdocs_component")
    }

    shutil.rmtree(OUTPUT_DIR, ignore_errors=True)
    OUTPUT_DIR.mkdir(parents=True)
    assets_by_alias = {}
    for source, normalized_source, _ in prepared_sources:
        for asset in normalized_source["assets"]:
            input_path = NORMALIZED_DIR / source["id"] / asset["path"]
            output_relative = Path("assets") / source["id"] / asset["path"]
            output_path = OUTPUT_DIR / output_relative
            output_path.parent.mkdir(parents=True, exist_ok=True)
            shutil.copy2(input_path, output_path)
            aliases = {asset["path"]}
            docs_dir = source.get("navigation", {}).get("docs_dir")
            if docs_dir and asset["path"].startswith(f"{docs_dir}/"):
                aliases.add(asset["path"].removeprefix(f"{docs_dir}/"))
            for alias in aliases:
                assets_by_alias[(source["id"], alias)] = output_relative.as_posix()

    validation = {
        "rewritten_links": 0,
        "external_links": 0,
        "site_relative_links": 0,
        "unresolved": [],
        "capped_headings": 0,
    }
    output = [
        "# Provider Journey Master Documentation",
        "",
        "> Generated proof-of-concept output. Review before use or publication.",
        "",
        "## Contents",
        "",
    ]
    for source, _, source_documents in prepared_sources:
        source_anchor = slugify(f"source--{source['id']}")
        output.append(f"- [{source['title']}](#{source_anchor})")
        output.extend(
            f"    - [{entry['title']}](#{entry['anchor']})"
            for entry in toc_entries_for_source(source_documents)
        )

    for source, _, source_documents in prepared_sources:
        source_anchor = slugify(f"source--{source['id']}")
        output.extend(["", f"# {source['title']} {{#{source_anchor}}}", ""])

        for document in source_documents:
            output.extend(
                [
                    f"<!-- source: {provenance(source, document)} -->",
                    "",
                    f"## {document['title']} {{#{document['anchor']}}}",
                    "",
                ]
            )
            in_fence = False
            for line_number, line in enumerate(document["lines"]):
                stripped = line.lstrip()
                if stripped.startswith(("```", "~~~")):
                    in_fence = not in_fence

                if not in_fence and LEGACY_ANCHOR_PATTERN.match(line):
                    continue

                heading = document["headings"].get(line_number)
                if heading and not in_fence:
                    if heading["skip"]:
                        continue
                    if heading["capped"]:
                        validation["capped_headings"] += 1
                    output.extend(
                        [
                            (
                                f"{'#' * heading['output_level']} {heading['title']} "
                                f"{{#{heading['anchor']}}}"
                            ),
                        ]
                    )
                elif in_fence:
                    output.append(line)
                else:
                    output.append(
                        rewrite_line(
                            line,
                            document,
                            documents_by_alias,
                            sources_by_component,
                            assets_by_alias,
                            validation,
                        )
                    )
            output.append("")

    MASTER_PATH.write_text("\n".join(output).rstrip() + "\n", encoding="utf-8")

    report = [
        "# Validation report",
        "",
        f"- Documents assembled: {len(documents)}",
        f"- Internal links rewritten: {validation['rewritten_links']}",
        f"- External links preserved: {validation['external_links']}",
        f"- Site-relative application links preserved: {validation['site_relative_links']}",
        f"- Unresolved links: {len(validation['unresolved'])}",
        f"- Heading levels capped at H6: {validation['capped_headings']}",
        "",
        "## Source navigation",
        "",
    ]
    for source, _, _ in prepared_sources:
        unlisted = source.get("navigation", {}).get("unlisted_files", [])
        if unlisted:
            report.append(f"- **{source['title']}:** appended files absent from source navigation:")
            report.extend(f"  - `{path}`" for path in unlisted)
        else:
            report.append(f"- **{source['title']}:** all selected files are in source navigation.")

    report.extend(["", "## Unresolved links", ""])
    if validation["unresolved"]:
        report.extend(
            (
                f"- `{item['source']}` → `{item['target']}`: {item['reason']}."
                for item in validation["unresolved"]
            )
        )
    else:
        report.append("- None.")

    REPORT_PATH.write_text("\n".join(report) + "\n", encoding="utf-8")
    print(f"Assembled {len(documents)} documents into {MASTER_PATH.relative_to(PROJECT_ROOT)}")
    print(
        f"Validation found {len(validation['unresolved'])} unresolved links and "
        f"{validation['capped_headings']} capped headings"
    )
    print(f"Wrote {REPORT_PATH.relative_to(PROJECT_ROOT)}")


if __name__ == "__main__":
    main()
