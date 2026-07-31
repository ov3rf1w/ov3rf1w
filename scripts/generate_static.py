from __future__ import annotations

import html
from pathlib import Path

from svg_theme import ACCENT, BG, FG, LINE, MUTED, font_css, shell, svg_document

ROOT = Path(__file__).resolve().parents[1]
ASSETS = ROOT / "assets"
FONTS = ASSETS / "fonts"


def hero() -> str:
    css = font_css(FONTS)
    grid = []
    for x in range(40, 1000, 40):
        grid.append(f'<path d="M{x} 0V330" stroke="{LINE}" stroke-opacity=".24"/>')
    for y in range(30, 330, 30):
        grid.append(f'<path d="M0 {y}H1000" stroke="{LINE}" stroke-opacity=".2"/>')
    body = shell(1000, 330) + f'''
<g>{''.join(grid)}</g>
<path d="M0 258 C180 210 285 315 475 246 S780 195 1000 250" fill="none" stroke="{ACCENT}" stroke-opacity=".22"/>
<path d="M0 282 C190 234 315 324 505 270 S790 220 1000 278" fill="none" stroke="{ACCENT}" stroke-opacity=".1"/>
<circle cx="916" cy="72" r="4" fill="{ACCENT}"/>
<text x="56" y="62" fill="{ACCENT}" font-family="'Geist Mono'" font-size="13" letter-spacing="3">OV3RF1W / STRUCTIVA</text>
<text x="53" y="155" fill="{FG}" font-family="'Archivo'" font-weight="700" font-size="70" letter-spacing="-2">RAPHAEL</text>
<text x="53" y="224" fill="{FG}" font-family="'Archivo'" font-weight="700" font-size="70" letter-spacing="-2">WAGNER<tspan fill="{ACCENT}">.</tspan></text>
<text x="58" y="273" fill="{MUTED}" font-family="'Manrope'" font-size="17">Web systems, design and automation from Austria.</text>
<text x="944" y="306" text-anchor="end" fill="{MUTED}" font-family="'Geist Mono'" font-size="11" letter-spacing="2">BUILD / REFINE / SHIP</text>
'''
    return svg_document(1000, 330, body, css)


def section(title: str, index: str) -> str:
    css = font_css(FONTS)
    safe_title = html.escape(title)
    body = shell(1000, 92) + f'''
<text x="34" y="34" fill="{ACCENT}" font-family="'Geist Mono'" font-size="11" letter-spacing="2">{index}</text>
<text x="34" y="69" fill="{FG}" font-family="'Archivo'" font-weight="700" font-size="29" letter-spacing="-.5">{safe_title}</text>
<path d="M350 59H958" stroke="{LINE}"/>
<circle cx="958" cy="59" r="3" fill="{ACCENT}"/>
'''
    return svg_document(1000, 92, body, css)


def main() -> None:
    ASSETS.mkdir(parents=True, exist_ok=True)
    (ASSETS / "hero.svg").write_text(hero(), encoding="utf-8")
    sections = {
        "section-work.svg": ("SELECTED WORK", "01 / WORK"),
        "section-stack.svg": ("STACK & APPROACH", "02 / SYSTEM"),
        "section-stats.svg": ("LIVE GITHUB SIGNAL", "03 / ACTIVITY"),
    }
    for filename, (title, index) in sections.items():
        (ASSETS / filename).write_text(section(title, index), encoding="utf-8")


if __name__ == "__main__":
    main()
