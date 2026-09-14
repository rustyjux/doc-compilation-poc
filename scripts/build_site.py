from __future__ import annotations

import shutil
import subprocess
import sys
from pathlib import Path


PROJECT_ROOT = Path(__file__).resolve().parents[1]
DIST_DIR = PROJECT_ROOT / "dist"
PAGE_DIR = PROJECT_ROOT / ".work" / "pages"
SITE_DIR = PROJECT_ROOT / "site"


def add_pdf_link(markdown: str) -> str:
    lines = markdown.splitlines()
    if not lines or not lines[0].startswith("# "):
        raise ValueError("Expected the master document to start with an H1")
    lines[1:1] = [
        "",
        "[Download PDF](master.pdf){ .md-button .md-button--primary }",
    ]
    return "\n".join(lines) + "\n"


def main() -> None:
    master_path = DIST_DIR / "master.md"
    pdf_path = DIST_DIR / "master.pdf"
    report_path = DIST_DIR / "validation-report.md"
    for required_path in (master_path, pdf_path, report_path):
        if not required_path.is_file():
            raise FileNotFoundError(f"Required publication file does not exist: {required_path}")

    shutil.rmtree(PAGE_DIR, ignore_errors=True)
    PAGE_DIR.mkdir(parents=True)
    (PAGE_DIR / "index.md").write_text(
        add_pdf_link(master_path.read_text(encoding="utf-8")),
        encoding="utf-8",
    )
    shutil.copy2(pdf_path, PAGE_DIR / pdf_path.name)
    shutil.copy2(report_path, PAGE_DIR / report_path.name)

    asset_dir = DIST_DIR / "assets"
    if asset_dir.is_dir():
        shutil.copytree(asset_dir, PAGE_DIR / "assets")

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
