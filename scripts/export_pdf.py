from __future__ import annotations

import subprocess
from pathlib import Path

from expand_tabs import prepare_pdf_markdown
from install_pandoc import PANDOC_PATH
from install_typst import TYPST_PATH


PROJECT_ROOT = Path(__file__).resolve().parents[1]
MASTER_PATH = PROJECT_ROOT / "dist" / "master.md"
PDF_MARKDOWN_PATH = PROJECT_ROOT / ".work" / "master.pdf.md"
PDF_PATH = PROJECT_ROOT / "dist" / "master.pdf"
PDF_CODEBLOCK_STYLE = PROJECT_ROOT / "templates" / "pdf-codeblocks.typ"


def main() -> None:
    if not MASTER_PATH.is_file():
        raise FileNotFoundError("Run assemble_master.py before exporting PDF")
    if not PANDOC_PATH.is_file():
        raise FileNotFoundError("Run install_pandoc.py before exporting PDF")
    if not TYPST_PATH.is_file():
        raise FileNotFoundError("Run install_typst.py before exporting PDF")

    PDF_MARKDOWN_PATH.parent.mkdir(parents=True, exist_ok=True)
    PDF_MARKDOWN_PATH.write_text(
        prepare_pdf_markdown(MASTER_PATH.read_text(encoding="utf-8")),
        encoding="utf-8",
    )

    result = subprocess.run(
        [
            str(PANDOC_PATH),
            str(PDF_MARKDOWN_PATH),
            "--from=markdown+header_attributes",
            f"--pdf-engine={TYPST_PATH}",
            f"--resource-path={MASTER_PATH.parent}",
            f"--include-in-header={PDF_CODEBLOCK_STYLE}",
            f"--output={PDF_PATH}",
        ],
        cwd=PROJECT_ROOT,
        capture_output=True,
        text=True,
    )
    if result.returncode != 0:
        detail = result.stderr.strip() or result.stdout.strip()
        raise RuntimeError(f"PDF export failed: {detail}")

    if not PDF_PATH.read_bytes().startswith(b"%PDF"):
        raise RuntimeError(f"PDF export produced an invalid file: {PDF_PATH}")
    print(
        f"Wrote {PDF_PATH.relative_to(PROJECT_ROOT)} "
        f"({PDF_PATH.stat().st_size / 1024:.1f} KiB)"
    )


if __name__ == "__main__":
    main()
