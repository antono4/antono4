#!/usr/bin/env python3
"""Post-process the GitBlock 3D contribution SVG into a colorful neon look.

The upstream generator (yoshi389111/github-profile-3d-contrib) overwrites
profile-gitblock.svg on every run, so all visual work is applied here instead of
by hand-editing the file.

Usage:
    python scripts/enhance_gitblock.py [--theme rainbow|cyber] [path/to/svg]

The file is rewritten in place. Default theme: rainbow.
"""
from __future__ import annotations

import argparse
import random
import re

WIDTH = 1280
HEIGHT = 850


def _clamp(value: float) -> int:
    return max(0, min(255, int(round(value))))


def hex_to_rgb(color: str):
    color = color.lstrip("#")
    return tuple(int(color[i : i + 2], 16) for i in (0, 2, 4))


def rgb_to_hex(r: float, g: float, b: float) -> str:
    return "#%02x%02x%02x" % (_clamp(r), _clamp(g), _clamp(b))


def shade(color: str, factor: float) -> str:
    """Darken (factor < 1) or lighten toward white (factor > 1) a hex color."""
    r, g, b = hex_to_rgb(color)
    if factor <= 1:
        return rgb_to_hex(r * factor, g * factor, b * factor)
    t = factor - 1
    return rgb_to_hex(r + (255 - r) * t, g + (255 - g) * t, b + (255 - b) * t)


def build_levels(base_colors: dict) -> dict:
    """Expand one base color per level into (top, left, right, window) fills."""
    levels = {}
    for level, base in base_colors.items():
        if level == 0:
            levels[0] = (
                base,
                shade(base, 0.75),
                shade(base, 0.55),
                shade(base, 2.4),
            )
            continue
        levels[level] = (
            base,
            shade(base, 0.55),
            shade(base, 0.38),
            shade(base, 1.5),
        )
    return levels


# --- themes -----------------------------------------------------------------
# level 0 is the empty/background cell, 1-4 are increasing contribution counts.
THEMES = {
    "rainbow": {
        "base_colors": {
            0: "#141c30",
            1: "#22d3ee",  # cyan
            2: "#4ade80",  # green
            3: "#fbbf24",  # amber
            4: "#f472b6",  # pink
        },
        "bg": (
            (0.0, "#1a0b2e"),
            (0.25, "#0b1b3a"),
            (0.5, "#06301f"),
            (0.75, "#3a2a06"),
            (1.0, "#3a0b22"),
        ),
        "title": ("#ff5f6d", "#ffc371", "#7dffb0", "#4dd8ff", "#c084fc"),
        "accent": "#8b5cf6",
        "accent_2": "#f472b6",
        "star_colors": ("#ff5f6d", "#ffc371", "#7dffb0", "#4dd8ff", "#c084fc"),
        "fill_strong": "#c084fc",
        "fill_weak": "#8b93b8",
        "stroke_weak": "#3b4a7a",
        "radar": "#f472b6",
        "scanline": "#ffffff",
        "sweep": ("#ff3b3b", "#ffd23b", "#5dff8a", "#3bd6ff", "#6a5bff", "#ff3bd6"),
    },
    "cyber": {
        "base_colors": {
            0: "#101a2e",
            1: "#0e4d3a",
            2: "#0f7a52",
            3: "#12b06a",
            4: "#24ff9b",
        },
        "bg": ((0.0, "#05070f"), (0.55, "#080e1d"), (1.0, "#0b1424")),
        "title": ("#4dd8ff", "#24ff9b", "#4dd8ff"),
        "accent": "#24ff9b",
        "accent_2": "#4dd8ff",
        "star_colors": ("#bfefff",),
        "fill_strong": "#7dffd0",
        "fill_weak": "#5f7fa8",
        "stroke_weak": "#2c5a7a",
        "radar": "#24ff9b",
        "scanline": "#7dffd0",
    },
}


def build_style(theme: dict) -> str:
    levels = build_levels(theme["base_colors"])
    lines = [
        '* { font-family: "Ubuntu", "Helvetica", "Arial", sans-serif; }',
        ".fill-bg { fill: #05070f; }",
        ".fill-fg { fill: #eef2ff; }",
        ".stroke-fg { stroke: #eef2ff; }",
        f'.fill-strong {{ fill: {theme["fill_strong"]}; }}',
        f'.fill-weak {{ fill: {theme["fill_weak"]}; }}',
        f'.stroke-weak {{ stroke: {theme["stroke_weak"]}; }}',
        f'.radar {{ stroke: {theme["radar"]}; fill: {theme["radar"]}; '
        "fill-opacity: 0.22; }",
    ]
    for level, (top, left, right, win) in levels.items():
        lines.append(f".cont-top-bg-{level} {{ fill: {top}; }}")
        lines.append(f".cont-top-fg-{level} {{ fill: {win}; }}")
        lines.append(f".cont-left-bg-{level} {{ fill: {left}; }}")
        lines.append(f".cont-left-fg-{level} {{ fill: {win}; }}")
        lines.append(f".cont-right-bg-{level} {{ fill: {right}; }}")
        lines.append(f".cont-right-fg-{level} {{ fill: {win}; }}")
    return "\n".join(lines)


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


def build_defs(theme: dict) -> str:
    glow = []
    for level in range(5):
        glow.append(
            f'<filter id="glow{level}" x="-60%" y="-60%" width="220%" height="220%">'
            f'<feGaussianBlur stdDeviation="{1.1 + level * 0.5:.1f}" result="b"/>'
            '<feMerge><feMergeNode in="b"/><feMergeNode in="b"/>'
            '<feMergeNode in="SourceGraphic"/></feMerge></filter>'
        )

    bg_stops = "".join(
        f'<stop offset="{offset:.3f}" stop-color="{c}"/>'
        for offset, c in theme["bg"]
    )
    title_stops = "".join(
        f'<stop offset="{i / (len(theme["title"]) - 1):.3f}" stop-color="{c}"/>'
        for i, c in enumerate(theme["title"])
    )
    scanline = (
        '<pattern id="scanlines" width="4" height="4" patternUnits="userSpaceOnUse">'
        '<rect width="4" height="4" fill="#000000" opacity="0"/>'
        f'<rect width="4" height="1" fill="{theme["scanline"]}" opacity="0.07"/>'
        "</pattern>"
    )
    return (
        "<defs>"
        '<linearGradient id="cyberBg" x1="0" y1="0" x2="0" y2="1">'
        + bg_stops
        + "</linearGradient>"
        '<radialGradient id="cyberVignette" cx="0.5" cy="0.45" r="0.75">'
        '<stop offset="0.55" stop-color="#000000" stop-opacity="0"/>'
        '<stop offset="1" stop-color="#000000" stop-opacity="0.65"/>'
        "</radialGradient>"
        '<linearGradient id="titleGrad" x1="0" y1="0" x2="1" y2="0">'
        + title_stops
        + "</linearGradient>"
        '<filter id="softGlow" x="-40%" y="-40%" width="180%" height="180%">'
        '<feGaussianBlur stdDeviation="2.4" result="b"/>'
        '<feMerge><feMergeNode in="b"/><feMergeNode in="SourceGraphic"/></feMerge>'
        "</filter>"
        '<filter id="titleGlow" x="-30%" y="-80%" width="160%" height="260%">'
        '<feGaussianBlur stdDeviation="3.2" result="b"/>'
        '<feMerge><feMergeNode in="b"/><feMergeNode in="b"/>'
        '<feMergeNode in="SourceGraphic"/></feMerge></filter>'
        + scanline
        + "".join(glow)
        + _sweep_gradient(theme)
        + "</defs>"
    )


def _sweep_gradient(theme: dict) -> str:
    """Horizontal rainbow band blended over the city (see build_overlay)."""
    sweep = theme.get("sweep")
    if not sweep:
        return ""
    stops = "".join(
        f'<stop offset="{i / (len(sweep) - 1):.3f}" stop-color="{c}"/>'
        for i, c in enumerate(sweep)
    )
    return (
        '<linearGradient id="rainbowSweep" x1="0" y1="0" x2="1" y2="0">'
        + stops
        + "</linearGradient>"
    )


def build_backdrop(theme: dict) -> str:
    rng = random.Random(42)
    stars = []
    for _ in range(150):
        x = rng.uniform(0, WIDTH)
        y = rng.uniform(0, 430)
        r = rng.choice([0.6, 0.9, 1.2, 1.6])
        base = rng.uniform(0.12, 0.6)
        dur = rng.uniform(2.5, 6.0)
        delay = rng.uniform(0, 5)
        color = rng.choice(theme["star_colors"])
        stars.append(
            f'<circle cx="{x:.0f}" cy="{y:.0f}" r="{r}" fill="{color}" '
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
        f'<g stroke="{theme["accent"]}" stroke-opacity="0.05" stroke-width="1">'
        f'{"".join(grid)}</g>'
        f'<g>{"".join(stars)}</g>'
        f'<line x1="0" y1="470" x2="{WIDTH}" y2="470" stroke="{theme["accent"]}" '
        'stroke-opacity="0.16" stroke-width="1"/>'
    )


def build_title(theme: dict) -> str:
    cx = WIDTH / 2
    return (
        '<g filter="url(#titleGlow)">'
        f'<text x="{cx:.0f}" y="52" text-anchor="middle" fill="url(#titleGrad)" '
        'style="font-size: 34px; font-weight: 700; letter-spacing: 12px;">'
        "CONTRIBUTION CITY</text>"
        "</g>"
        f'<text x="{cx:.0f}" y="76" text-anchor="middle" fill="{theme["fill_weak"]}" '
        'style="font-size: 13px; letter-spacing: 5px;">'
        "@antono4 · LIVE 3D CONTRIBUTION MAP</text>"
        f'<rect x="{cx - 130:.0f}" y="88" width="260" height="2" fill="url(#titleGrad)" '
        'opacity="0.75">'
        '<animate attributeName="opacity" values="0.25;0.9;0.25" dur="4s" '
        'repeatCount="indefinite"/></rect>'
        f'<g fill="none" stroke="{theme["accent_2"]}" stroke-opacity="0.4" stroke-width="2">'
        '<path d="M24 24 h46 M24 24 v46"/><path d="M1256 24 h-46 M1256 24 v46"/>'
        '<path d="M24 826 h46 M24 826 v-46"/><path d="M1256 826 h-46 M1256 826 v-46"/>'
        "</g>"
    )


def build_overlay(theme: dict) -> str:
    parts = []
    if theme.get("sweep"):
        parts.append(
            f'<rect x="0" y="0" width="{WIDTH}" height="{HEIGHT}" '
            'fill="url(#rainbowSweep)" opacity="0.6" '
            'style="mix-blend-mode: color;"/>'
        )
    parts.append(
        f'<rect x="0" y="0" width="{WIDTH}" height="{HEIGHT}" fill="url(#cyberVignette)"/>'
    )
    parts.append(
        f'<rect x="0" y="0" width="{WIDTH}" height="{HEIGHT}" fill="url(#scanlines)" '
        'opacity="0.5" style="mix-blend-mode: overlay;"/>'
    )
    return "".join(parts)


def enhance(svg: str, theme: dict) -> str:
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
        + build_style(theme)
        + "</style>"
        + svg[style_end:]
    )

    # 2. extra gradients/filters/pattern
    svg = svg.replace("</defs>", build_defs(theme) + "</defs>", 1)

    # 3. backdrop + title replace the flat background rect
    bg = '<rect x="0" y="0" width="1280" height="850" class="fill-bg"></rect>'
    if bg not in svg:
        bg = '<rect x="0" y="0" width="1280" height="850" class="fill-bg"/>'
    if bg not in svg:
        raise SystemExit("background rect not found")
    svg = svg.replace(bg, build_backdrop(theme) + build_title(theme), 1)

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
        svg = svg[:footer] + build_overlay(theme) + svg[footer:]

    # 7. footer text gets a soft neon glow
    footer = svg.rfind("<g>")
    if footer > 0:
        svg = svg[:footer] + '<g filter="url(#softGlow)">' + svg[footer + 3:]

    return svg


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--theme",
        choices=sorted(THEMES),
        default="rainbow",
        help="color theme (default: rainbow)",
    )
    parser.add_argument(
        "path",
        nargs="?",
        default="profile-3d-contrib/profile-gitblock.svg",
        help="path to the SVG to enhance in place",
    )
    args = parser.parse_args()

    with open(args.path, encoding="utf-8") as fh:
        svg = fh.read()

    out = enhance(svg, THEMES[args.theme])

    with open(args.path, "w", encoding="utf-8") as fh:
        fh.write(out)
    print(f"enhanced {args.path} [{args.theme}]: {len(svg)} -> {len(out)} bytes")


if __name__ == "__main__":
    main()
