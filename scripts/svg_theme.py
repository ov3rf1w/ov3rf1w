from __future__ import annotations

import base64
from pathlib import Path

BG = "#0e0d0c"
BG_RAISED = "#17150f"
FG = "#f4f1ea"
MUTED = "#a39b8c"
ACCENT = "#ff5b04"
ACCENT_SOFT = "#ff8a4d"
LINE = "#2a2722"


def _font_data(path: Path) -> str:
    return base64.b64encode(path.read_bytes()).decode("ascii")


def font_css(font_dir: Path, *, include_portrait: bool = False) -> str:
    declarations = [
        ("Archivo", "archivo-700.woff2", 700),
        ("Manrope", "manrope-600.woff2", 600),
        ("Geist Mono", "geist-mono-500.woff2", 500),
    ]
    if include_portrait:
        declarations.append(("JetBrains Mono", "jetbrains-mono-400.woff2", 400))

    return "\n".join(
        "@font-face{"
        f"font-family:'{family}';font-style:normal;font-weight:{weight};"
        f"src:url(data:font/woff2;base64,{_font_data(font_dir / filename)}) format('woff2');"
        "}"
        for family, filename, weight in declarations
    )


def svg_document(width: int, height: int, body: str, css: str = "") -> str:
    return f'''<svg xmlns="http://www.w3.org/2000/svg" width="{width}" height="{height}" viewBox="0 0 {width} {height}" role="img">
<style>{css}</style>
{body}
</svg>
'''


def shell(width: int, height: int) -> str:
    return f'''
<rect width="{width}" height="{height}" rx="18" fill="{BG}"/>
<rect x="1" y="1" width="{width - 2}" height="{height - 2}" rx="17" fill="none" stroke="{LINE}"/>
'''
