from __future__ import annotations

import subprocess
import sys
from pathlib import Path


SCRIPT_DIR = Path(__file__).resolve().parent
STEPS = (
    "install_pandoc.py",
    "install_typst.py",
    "fetch_sources.py",
    "normalize_sources.py",
    "assemble_master.py",
    "export_pdf.py",
    "build_site.py",
)


def main() -> None:
    for step in STEPS:
        print(f"\n==> {step}", flush=True)
        subprocess.run([sys.executable, str(SCRIPT_DIR / step)], check=True)


if __name__ == "__main__":
    main()
