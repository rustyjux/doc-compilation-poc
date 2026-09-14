from __future__ import annotations

import re


TAB_MARKER = re.compile(r'^=== "([^"]+)"\s*$')
ADMONITION_MARKER = re.compile(r"^(!!!|\?\?\?\+?)\s+(.+?)\s*$")
ADMONITION_TITLE = re.compile(r'\s+"([^"]*)"\s*$')
EXTERNAL_LINK_PATTERN = re.compile(
    r"(?<!!)"  # do not match images
    r"\[([^\]]+)\]\((https?://[^)\s]+)(\s+\"[^\"]*\")?\)"
)


def mark_external_links(markdown: str, icon_path: str) -> str:
    """Embed a pop-out icon inside absolute http(s) Markdown link labels."""

    def replace(match: re.Match[str]) -> str:
        label, target, title = match.group(1), match.group(2), match.group(3) or ""
        if icon_path in label or "external-link.svg" in label:
            return match.group(0)
        icon = f"![]({icon_path}){{width=0.7em}}"
        return f"[{label}{icon}]({target}{title})"

    return EXTERNAL_LINK_PATTERN.sub(replace, markdown)


def _trim_blank_edges(lines: list[str]) -> list[str]:
    while lines and lines[0] == "":
        lines.pop(0)
    while lines and lines[-1] == "":
        lines.pop()
    return lines


def _quote_block(label: str, content: list[str]) -> list[str]:
    quoted = [f"> **{label}**", ">"]
    for line in content:
        quoted.append(f"> {line}" if line else ">")
    quoted.append("")
    return quoted


def _admonition_label(body: str) -> str:
    title_match = ADMONITION_TITLE.search(body)
    if title_match:
        title = title_match.group(1)
        type_and_modifiers = body[: title_match.start()].strip()
    else:
        title = None
        type_and_modifiers = body.strip()

    admonition_type = type_and_modifiers.split(maxsplit=1)[0]
    type_label = admonition_type.replace("-", " ").replace("_", " ").title()
    if title is None or title == "":
        return type_label
    return f"{type_label}: {title}"


def _collect_indented_block(lines: list[str], start: int) -> tuple[list[str], int]:
    content: list[str] = []
    index = start
    while index < len(lines):
        current = lines[index]
        if current == "" or current.startswith("    "):
            content.append(current[4:] if current.startswith("    ") else current)
            index += 1
            continue
        break
    return _trim_blank_edges(content), index


def expand_admonitions(markdown: str) -> str:
    """Convert admonition/details blocks into labeled blockquotes for PDF."""
    lines = markdown.splitlines()
    result: list[str] = []
    index = 0
    in_fence = False

    while index < len(lines):
        line = lines[index]
        stripped = line.lstrip()
        if stripped.startswith(("```", "~~~")):
            in_fence = not in_fence
            result.append(line)
            index += 1
            continue
        if in_fence or not (marker := ADMONITION_MARKER.match(line)):
            result.append(line)
            index += 1
            continue

        label = _admonition_label(marker.group(2))
        content, index = _collect_indented_block(lines, index + 1)
        # Expand nested admonitions/tabs that may appear inside this block.
        nested = prepare_pdf_markdown("\n".join(content)).rstrip("\n").splitlines()
        result.extend(_quote_block(label, nested))

    return "\n".join(result).rstrip() + "\n"


def expand_tabs(markdown: str) -> str:
    """Convert pymdownx.tabbed groups into labeled blockquotes for PDF."""
    lines = markdown.splitlines()
    result: list[str] = []
    index = 0
    in_fence = False

    while index < len(lines):
        line = lines[index]
        stripped = line.lstrip()
        if stripped.startswith(("```", "~~~")):
            in_fence = not in_fence
            result.append(line)
            index += 1
            continue
        if in_fence or not TAB_MARKER.match(line):
            result.append(line)
            index += 1
            continue

        while index < len(lines) and (marker := TAB_MARKER.match(lines[index])):
            label = marker.group(1)
            content, index = _collect_indented_block(lines, index + 1)
            nested = prepare_pdf_markdown("\n".join(content)).rstrip("\n").splitlines()
            result.extend(_quote_block(label, nested))

    return "\n".join(result).rstrip() + "\n"


def prepare_pdf_markdown(markdown: str, external_link_icon: str | None = None) -> str:
    """Apply PDF-oriented Markdown transforms for Material syntax."""
    transformed = expand_tabs(expand_admonitions(markdown))
    if external_link_icon:
        transformed = mark_external_links(transformed, external_link_icon)
    return transformed
