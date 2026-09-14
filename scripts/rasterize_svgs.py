from __future__ import annotations

import os
import re
import shutil
import subprocess
import tempfile
from pathlib import Path

from PIL import Image


PROJECT_ROOT = Path(__file__).resolve().parents[1]
ASSETS_DIR = PROJECT_ROOT / "dist" / "assets"
SCALE = 2
LIGHT_DARK_PATTERN = re.compile(r"light-dark\(\s*([^,]+?)\s*,\s*[^)]+\)")
IMAGE_PATTERN = re.compile(
    r"(?P<bang>!?)\[(?P<label>[^\]]*)\]\((?P<target>[^)\s]+\.svg)(?P<suffix>[^)]*)\)"
)

CHROME_CANDIDATES = (
    os.environ.get("CHROME_PATH", ""),
    "/Applications/Google Chrome.app/Contents/MacOS/Google Chrome",
    "/Applications/Chromium.app/Contents/MacOS/Chromium",
    "google-chrome",
    "google-chrome-stable",
    "chromium",
    "chromium-browser",
)


def find_chrome() -> str:
    for candidate in CHROME_CANDIDATES:
        if not candidate:
            continue
        path = Path(candidate)
        if path.is_file():
            return str(path)
        resolved = shutil.which(candidate)
        if resolved:
            return resolved
    raise FileNotFoundError(
        "Chrome/Chromium is required to rasterize draw.io SVGs for PDF. "
        "Install Chrome or set CHROME_PATH."
    )


def svg_dimensions(svg: str) -> tuple[int, int]:
    width_match = re.search(r'\bwidth="(\d+(?:\.\d+)?)(?:px)?"', svg)
    height_match = re.search(r'\bheight="(\d+(?:\.\d+)?)(?:px)?"', svg)
    if width_match and height_match:
        return int(float(width_match.group(1))), int(float(height_match.group(1)))

    viewbox = re.search(r'\bviewBox="([^"]+)"', svg)
    if viewbox:
        parts = viewbox.group(1).replace(",", " ").split()
        if len(parts) == 4:
            return int(float(parts[2])), int(float(parts[3]))
    raise ValueError("Could not determine SVG width and height")


def prepare_svg_for_pdf(svg: str) -> str:
    # Typst/PDF have no dark-mode context; keep the light branch.
    prepared = LIGHT_DARK_PATTERN.sub(r"\1", svg)
    return prepared.replace("color-scheme: light dark", "color-scheme: light")


def rasterize_svg(chrome: str, svg_path: Path, png_path: Path) -> None:
    svg = prepare_svg_for_pdf(svg_path.read_text(encoding="utf-8"))
    width, height = svg_dimensions(svg)
    html = f"""<!DOCTYPE html>
<html>
<head>
  <meta charset="utf-8">
  <style>
    html, body {{ margin: 0; padding: 0; background: #fff; color-scheme: light; }}
    svg {{ display: block; }}
  </style>
</head>
<body>
{svg}
</body>
</html>
"""
    with tempfile.TemporaryDirectory() as temporary_directory:
        html_path = Path(temporary_directory) / "diagram.html"
        screenshot_path = Path(temporary_directory) / "screenshot.png"
        html_path.write_text(html, encoding="utf-8")
        chrome_args = [
            chrome,
            "--headless=new",
            "--disable-gpu",
            "--hide-scrollbars",
            "--no-first-run",
            "--no-default-browser-check",
            "--force-color-profile=srgb",
            "--default-background-color=ffffffff",
            f"--force-device-scale-factor={SCALE}",
            f"--window-size={width},{height}",
            f"--screenshot={screenshot_path}",
        ]
        if os.environ.get("CI"):
            chrome_args.extend(["--no-sandbox", "--disable-dev-shm-usage"])
        chrome_args.append(html_path.resolve().as_uri())
        result = subprocess.run(
            chrome_args,
            capture_output=True,
            text=True,
        )
        if result.returncode != 0 or not screenshot_path.is_file():
            detail = result.stderr.strip() or result.stdout.strip()
            raise RuntimeError(f"Failed to rasterize {svg_path}: {detail}")

        image = Image.open(screenshot_path).convert("RGBA")
        expected = (width * SCALE, height * SCALE)
        if image.size != expected:
            image = image.crop((0, 0, expected[0], expected[1]))
        png_path.parent.mkdir(parents=True, exist_ok=True)
        image.save(png_path)


def rewrite_svg_images(markdown: str, replacements: dict[str, str]) -> str:
    def replace(match: re.Match[str]) -> str:
        target = match.group("target")
        rewritten = replacements.get(target, target)
        return (
            f"{match.group('bang')}[{match.group('label')}]"
            f"({rewritten}{match.group('suffix')})"
        )

    return IMAGE_PATTERN.sub(replace, markdown)


def rasterize_dist_svgs() -> dict[str, str]:
    if not ASSETS_DIR.is_dir():
        return {}
    chrome = find_chrome()
    replacements: dict[str, str] = {}
    for svg_path in sorted(ASSETS_DIR.rglob("*.svg")):
        png_path = svg_path.with_suffix(".png")
        print(f"Rasterizing {svg_path.relative_to(PROJECT_ROOT)} for PDF...")
        rasterize_svg(chrome, svg_path, png_path)
        svg_relative = svg_path.relative_to(PROJECT_ROOT / "dist").as_posix()
        png_relative = png_path.relative_to(PROJECT_ROOT / "dist").as_posix()
        replacements[svg_relative] = png_relative
    return replacements
