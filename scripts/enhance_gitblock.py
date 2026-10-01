#!/usr/bin/env python3
"""Post-process the GitBlock 3D contribution SVG into a neon "cyber city" look.

The upstream generator (yoshi389111/github-profile-3d-contrib) overwrites
profile-gitblock.svg on every run, so all visual work is applied here instead of
by hand-editing the file.

Usage:
    python scripts/enhance_gitblock.py [path/to/profile-gitblock.svg]

The file is rewritten in place.
"""
from __future__ import annotations

import random
import re
import sys

WIDTH = 1280
HEIGHT = 850
ACCENT = "#24ff9b"
ACCENT_2 = "#4dd8ff"

# level -> (top, left, right, window) fills. Level 0 is the empty/background
# cell, 1-4 are the increasing contribution intensities.
NEON_LEVELS = {
    0: ("#101a2e", "#0b1220", "#070c16", "#2b3f63"),
    1: ("#0e4d3a", "#0a3b2d", "#072a20", "#7dffb0"),
    2: ("#0f7a52", "#0a5c3e", "#07402b", "#9dffc4"),
    3: ("#12b06a", "#0d8a51", "#0a613a", "#c8ffe0"),
    4: ("#24ff9b", "#17d97c", "#0fa85e", "#ffffff"),
}

STYLE_OVERRIDES = """* { font-family: "Ubuntu", "Helvetica", "Arial", sans-serif; }
.fill-bg { fill: #05070f; }
.fill-fg { fill: #e8fbff; }
.stroke-fg { stroke: #e8fbff; }
.fill-strong { fill: #7dffd0; }
.fill-weak { fill: #5f7fa8; }
.stroke-weak { stroke: #2c5a7a; }
.radar { stroke: #24ff9b; fill: #24ff9b; fill-opacity: 0.22; }
"""

SCANLINE_PATTERN = (
    '<pattern id="scanlines" width="4" height="4" patternUnits="userSpaceOnUse">'
    '<rect width="4" height="4" fill="#000000" opacity="0"/>'
    '<rect width="4" height="1" fill="#7dffd0" opacity="0.07"/>'
    "</pattern>"
)


def build_level_css() -> str:
    out = []
    for level, (top, left, right, win) in NEON_LEVELS.items():
        out.append(f".cont-top-bg-{level} {{ fill: {top}; }}")
        out.append(f".cont-top-fg-{level} {{ fill: {win}; }}")
        out.append(f".cont-left-bg-{level} {{ fill: {left}; }}")
        out.append(f".cont-left-fg-{level} {{ fill: {win}; }}")
        out.append(f".cont-right-bg-{level} {{ fill: {right}; }}")
        out.append(f".cont-right-fg-{level} {{ fill: {win}; }}")
    return "\n".join(out)


def neon_rect(match: re.Match) -> str:
    rect = match.group(0)
    m = re.search(r'fill="url\(#pattern_(\d)_(top|left|right)\)"', rect)
    if not m:
        return rect
    level = int(m.group(1))
    if "filter=" not in rect:
        rect = rect.replace("<rect ", f'<rect filter="url(#glow{level})" ', 1)
    return rect


def extract_radar(svg: str):
    """Return (start, end) offsets of the radar group element."""
    anchor = svg.find('<g transform="translate(980, 284.5)">')
    if anchor < 0:
        return None
    depth = 0
    for m in re.finditer(r"<g\b[^>]*>|</g>", svg[anchor:]):
        if m.group(0).startswith("</"):
            depth -= 1
            if depth == 0:
                return anchor, anchor + m.end()
        else:
            depth += 1
    return None


def build_defs() -> str:
    glow = []
    for level in range(5):
        glow.append(
            f'<filter id="glow{level}" x="-60%" y="-60%" width="220%" height="220%">'
            f'<feGaussianBlur stdDeviation="{1.1 + level * 0.5:.1f}" result="b"/>'
            '<feMerge><feMergeNode in="b"/><feMergeNode in="b"/>'
            '<feMergeNode in="SourceGraphic"/></feMerge></filter>'
        )
    return (
        "<defs>"
        '<linearGradient id="cyberBg" x1="0" y1="0" x2="0" y2="1">'
        '<stop offset="0" stop-color="#05070f"/>'
        '<stop offset="0.55" stop-color="#080e1d"/>'
        '<stop offset="1" stop-color="#0b1424"/>'
        "</linearGradient>"
        '<radialGradient id="cyberVignette" cx="0.5" cy="0.45" r="0.75">'
        '<stop offset="0.55" stop-color="#000000" stop-opacity="0"/>'
        '<stop offset="1" stop-color="#000000" stop-opacity="0.65"/>'
        "</radialGradient>"
        '<linearGradient id="titleGrad" x1="0" y1="0" x2="1" y2="0">'
        '<stop offset="0" stop-color="#4dd8ff"/>'
        '<stop offset="0.5" stop-color="#24ff9b"/>'
        '<stop offset="1" stop-color="#4dd8ff"/>'
        "</linearGradient>"
        '<filter id="softGlow" x="-40%" y="-40%" width="180%" height="180%">'
        '<feGaussianBlur stdDeviation="2.4" result="b"/>'
        '<feMerge><feMergeNode in="b"/><feMergeNode in="SourceGraphic"/></feMerge>'
        "</filter>"
        '<filter id="titleGlow" x="-30%" y="-80%" width="160%" height="260%">'
        '<feGaussianBlur stdDeviation="3.2" result="b"/>'
        '<feMerge><feMergeNode in="b"/><feMergeNode in="b"/>'
        '<feMergeNode in="SourceGraphic"/></feMerge></filter>'
        + SCANLINE_PATTERN
        + "".join(glow)
        + "</defs>"
    )


def build_backdrop() -> str:
    rng = random.Random(42)
    stars = []
    for _ in range(140):
        x = rng.uniform(0, WIDTH)
        y = rng.uniform(0, 430)
        r = rng.choice([0.6, 0.9, 1.2, 1.6])
        base = rng.uniform(0.12, 0.55)
        dur = rng.uniform(2.5, 6.0)
        delay = rng.uniform(0, 5)
        stars.append(
            f'<circle cx="{x:.0f}" cy="{y:.0f}" r="{r}" fill="#bfefff" '
            f'opacity="{base:.2f}">'
            f'<animate attributeName="opacity" values="{base:.2f};0.05;{base:.2f}" '
            f'dur="{dur:.1f}s" begin="{delay:.1f}s" repeatCount="indefinite"/>'
            "</circle>"
        )

    grid = []
    for x in range(0, WIDTH + 1, 40):
        grid.append(f'<line x1="{x}" y1="0" x2="{x}" y2="{HEIGHT}"/>')
    for y in range(0, HEIGHT + 1, 40):
        grid.append(f'<line x1="0" y1="{y}" x2="{WIDTH}" y2="{y}"/>')

    return (
        f'<rect x="0" y="0" width="{WIDTH}" height="{HEIGHT}" fill="url(#cyberBg)"/>'
        f'<g stroke="{ACCENT}" stroke-opacity="0.05" stroke-width="1">{"".join(grid)}</g>'
        f'<g>{"".join(stars)}</g>'
        f'<line x1="0" y1="470" x2="{WIDTH}" y2="470" stroke="{ACCENT}" '
        'stroke-opacity="0.14" stroke-width="1"/>'
    )


def build_title() -> str:
    cx = WIDTH / 2
    return (
        '<g filter="url(#titleGlow)">'
        f'<text x="{cx:.0f}" y="52" text-anchor="middle" fill="url(#titleGrad)" '
        'style="font-size: 34px; font-weight: 700; letter-spacing: 12px;">'
        "CONTRIBUTION CITY</text>"
        "</g>"
        f'<text x="{cx:.0f}" y="76" text-anchor="middle" fill="#5f7fa8" '
        'style="font-size: 13px; letter-spacing: 5px;">'
        "@antono4 · LIVE 3D CONTRIBUTION MAP</text>"
        f'<rect x="{cx - 130:.0f}" y="88" width="260" height="2" fill="url(#titleGrad)" '
        'opacity="0.75">'
        '<animate attributeName="opacity" values="0.25;0.9;0.25" dur="4s" '
        'repeatCount="indefinite"/></rect>'
        f'<g fill="none" stroke="{ACCENT_2}" stroke-opacity="0.35" stroke-width="2">'
        '<path d="M24 24 h46 M24 24 v46"/><path d="M1256 24 h-46 M1256 24 v46"/>'
        '<path d="M24 826 h46 M24 826 v-46"/><path d="M1256 826 h-46 M1256 826 v-46"/>'
        "</g>"
    )


def build_overlay() -> str:
    return (
        f'<rect x="0" y="0" width="{WIDTH}" height="{HEIGHT}" fill="url(#cyberVignette)"/>'
        f'<rect x="0" y="0" width="{WIDTH}" height="{HEIGHT}" fill="url(#scanlines)" '
        'opacity="0.5" style="mix-blend-mode: overlay;"/>'
    )


def enhance(svg: str) -> str:
    if "CONTRIBUTION CITY" in svg:
        return svg

    # 1. palette + class overrides
    style_start = svg.find("<style>")
    style_end = svg.find("</style>")
    if style_start < 0 or style_end < 0:
        raise SystemExit("no <style> block found")
    style_end += len("</style>")
    svg = (
        svg[:style_start]
        + "<style>"
        + STYLE_OVERRIDES
        + build_level_css()
        + "</style>"
        + svg[style_end:]
    )

    # 2. extra gradients/filters/pattern
    svg = svg.replace("</defs>", build_defs() + "</defs>", 1)

    # 3. backdrop + title replace the flat background rect
    bg = '<rect x="0" y="0" width="1280" height="850" class="fill-bg"></rect>'
    if bg not in svg:
        bg = '<rect x="0" y="0" width="1280" height="850" class="fill-bg"/>'
    if bg not in svg:
        raise SystemExit("background rect not found")
    svg = svg.replace(bg, build_backdrop() + build_title(), 1)

    # 4. neon glow on every contribution block
    svg = re.sub(r"<rect\b[^>]*/>", neon_rect, svg)

    # 5. radar: spin the sweep + glow
    radar = extract_radar(svg)
    if radar:
        start, end = radar
        block = svg[start:end]
        block = block.replace(
            '<polygon class="radar"',
            '<polygon class="radar" filter="url(#softGlow)"',
            1,
        )
        block = block.replace(
            '<polygon class="radar"',
            '<animateTransform attributeName="transform" type="rotate" '
            'from="0" to="360" dur="26s" repeatCount="indefinite" additive="sum"/>'
            '<polygon class="radar"',
            1,
        )
        svg = svg[:start] + block + svg[end:]

    # 6. overlay above the city but below the footer stats
    footer = svg.rfind("<g>")
    if footer > 0:
        svg = svg[:footer] + build_overlay() + svg[footer:]

    # 7. footer text gets a soft neon glow
    footer = svg.rfind("<g>")
    if footer > 0:
        svg = svg[:footer] + '<g filter="url(#softGlow)">' + svg[footer + 3:]

    return svg


def main() -> None:
    path = (
        sys.argv[1]
        if len(sys.argv) > 1
        else "profile-3d-contrib/profile-gitblock.svg"
    )
    with open(path, encoding="utf-8") as fh:
        svg = fh.read()

    out = enhance(svg)

    with open(path, "w", encoding="utf-8") as fh:
        fh.write(out)
    print(f"enhanced {path}: {len(svg)} -> {len(out)} bytes")


if __name__ == "__main__":
    main()
