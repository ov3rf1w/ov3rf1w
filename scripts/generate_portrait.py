from __future__ import annotations

import argparse
import html
from pathlib import Path

import numpy as np
import cv2
from PIL import Image, ImageEnhance, ImageFilter, ImageOps

from svg_theme import ACCENT, BG, FG, LINE, MUTED, font_css, shell, svg_document

RAMP = "@%#sc*+=-:`. "


def subject_on_white(image: Image.Image) -> Image.Image:
    try:
        from rembg import remove

        rgba = image.convert("RGBA")
        cutout = remove(rgba)
        white = Image.new("RGBA", cutout.size, (255, 255, 255, 255))
        white.alpha_composite(cutout)
        return white.convert("RGB")
    except Exception:
        # Safe fallback for the deliberately plain dark source background.
        rgb = np.asarray(image.convert("RGB"), dtype=np.float32)
        luminance = rgb.mean(axis=2)
        mask = np.clip((luminance - 18.0) / 48.0, 0.0, 1.0)
        mask = np.asarray(Image.fromarray((mask * 255).astype("uint8")).filter(ImageFilter.GaussianBlur(2))) / 255.0
        composed = rgb * mask[..., None] + 255.0 * (1.0 - mask[..., None])
        return Image.fromarray(np.clip(composed, 0, 255).astype("uint8"), "RGB")


def ascii_rows(image: Image.Image, cols: int) -> list[str]:
    prepared = subject_on_white(image)
    gray = ImageOps.grayscale(prepared)
    gray = gray.filter(ImageFilter.GaussianBlur(0.25))
    gray = ImageOps.autocontrast(gray, cutoff=0.25)
    gray = ImageEnhance.Contrast(gray).enhance(1.12)

    width, height = gray.size
    rows = max(1, round(cols * (height / width) * 0.48))
    sample = np.asarray(gray.resize((cols, rows), Image.Resampling.LANCZOS), dtype=np.uint8)
    clean_background = sample >= 245
    filtered = cv2.bilateralFilter(sample, d=5, sigmaColor=24, sigmaSpace=24)
    clahe = cv2.createCLAHE(clipLimit=2.4, tileGridSize=(8, 8))
    enhanced = clahe.apply(filtered)
    sample = cv2.addWeighted(sample, 0.58, enhanced, 0.42, 0)
    sample[clean_background] = 255
    values = np.asarray(sample, dtype=np.float32) / 255.0
    values = np.power(values, 1.42)
    indices = np.clip((values * (len(RAMP) - 1)).astype(int), 0, len(RAMP) - 1)
    return ["".join(RAMP[index] for index in row).rstrip() for row in indices]


def render(rows: list[str], font_dir: Path) -> str:
    width, height = 1000, 620
    font_size = 9.1
    char_width = 5.52
    line_height = 10.6
    start_x, start_y = 28, 50
    css = font_css(font_dir, include_portrait=True)

    clips: list[str] = []
    texts: list[str] = []
    for index, row in enumerate(rows):
        y = start_y + index * line_height
        reveal_width = max(2.0, len(row) * char_width)
        begin = index * 0.075
        clips.append(
            f'<clipPath id="r{index}"><rect x="{start_x}" y="{y - font_size}" width="0" height="{line_height + 2}">'
            f'<animate attributeName="width" from="0" to="{reveal_width:.1f}" dur=".42s" begin="{begin:.3f}s" fill="freeze"/>'
            '</rect></clipPath>'
        )
        texts.append(
            f'<text x="{start_x}" y="{y:.1f}" clip-path="url(#r{index})" fill="{FG}" '
            f'font-family="\'JetBrains Mono\'" font-size="{font_size}" xml:space="preserve">{html.escape(row)}</text>'
        )
        texts.append(
            f'<rect x="{start_x}" y="{y - font_size + 1:.1f}" width="3.5" height="{font_size}" fill="{ACCENT}" opacity="0">'
            f'<animate attributeName="x" from="{start_x}" to="{start_x + reveal_width:.1f}" dur=".42s" begin="{begin:.3f}s" fill="freeze"/>'
            f'<set attributeName="opacity" to="1" begin="{begin:.3f}s"/><set attributeName="opacity" to="0" begin="{begin + .42:.3f}s"/>'
            '</rect>'
        )

    copy_x = 658
    body = shell(width, height) + f'''
<defs>{''.join(clips)}</defs>
<path d="M628 34V586" stroke="{LINE}"/>
<text x="{copy_x}" y="74" fill="{ACCENT}" font-family="'Geist Mono'" font-size="11" letter-spacing="2">ONE PERSON / FULL SYSTEM</text>
<text x="{copy_x}" y="133" fill="{FG}" font-family="'Archivo'" font-size="36">Technik, die</text>
<text x="{copy_x}" y="174" fill="{FG}" font-family="'Archivo'" font-size="36">Charakter zeigt<tspan fill="{ACCENT}">.</tspan></text>
<text x="{copy_x}" y="225" fill="{MUTED}" font-family="'Manrope'" font-size="15">Keine anonyme Agentur.</text>
<text x="{copy_x}" y="249" fill="{MUTED}" font-family="'Manrope'" font-size="15">Kein Baukasten-Look.</text>
<text x="{copy_x}" y="273" fill="{MUTED}" font-family="'Manrope'" font-size="15">Ein direkter Weg von der Idee</text>
<text x="{copy_x}" y="297" fill="{MUTED}" font-family="'Manrope'" font-size="15">bis zum laufenden System.</text>
<path d="M{copy_x} 345H950" stroke="{LINE}"/>
<text x="{copy_x}" y="380" fill="{FG}" font-family="'Manrope'" font-size="14">FOUNDER / DEVELOPER</text>
<text x="{copy_x}" y="408" fill="{MUTED}" font-family="'Geist Mono'" font-size="11" letter-spacing="1.5">STRUCTIVA · AUSTRIA</text>
<circle cx="{copy_x}" cy="472" r="4" fill="{ACCENT}"/>
<text x="{copy_x + 18}" y="477" fill="{MUTED}" font-family="'Geist Mono'" font-size="11">PORTRAIT PRINTS ONCE</text>
<text x="{copy_x + 18}" y="499" fill="{MUTED}" font-family="'Geist Mono'" font-size="11">THEN HOLDS THE FINAL FRAME</text>
{''.join(texts)}
'''
    return svg_document(width, height, body, css)


def render_mobile(rows: list[str], font_dir: Path) -> str:
    width, height = 600, 760
    font_size = 10.2
    char_width = 6.14
    line_height = 11.6
    start_x, start_y = 28, 54
    css = font_css(font_dir, include_portrait=True)
    clips: list[str] = []
    texts: list[str] = []
    for index, row in enumerate(rows):
        y = start_y + index * line_height
        reveal_width = max(2.0, len(row) * char_width)
        begin = index * 0.075
        clips.append(
            f'<clipPath id="m{index}"><rect x="{start_x}" y="{y - font_size}" width="0" height="{line_height + 2}">'
            f'<animate attributeName="width" from="0" to="{reveal_width:.1f}" dur=".42s" begin="{begin:.3f}s" fill="freeze"/>'
            '</rect></clipPath>'
        )
        texts.append(
            f'<text x="{start_x}" y="{y:.1f}" clip-path="url(#m{index})" fill="{FG}" '
            f'font-family="\'JetBrains Mono\'" font-size="{font_size}" xml:space="preserve">{html.escape(row)}</text>'
        )
        texts.append(
            f'<rect x="{start_x}" y="{y - font_size + 1:.1f}" width="4" height="{font_size}" fill="{ACCENT}" opacity="0">'
            f'<animate attributeName="x" from="{start_x}" to="{start_x + reveal_width:.1f}" dur=".42s" begin="{begin:.3f}s" fill="freeze"/>'
            f'<set attributeName="opacity" to="1" begin="{begin:.3f}s"/><set attributeName="opacity" to="0" begin="{begin + .42:.3f}s"/>'
            '</rect>'
        )

    body = shell(width, height) + f'''
<defs>{''.join(clips)}</defs>
<text x="28" y="30" fill="{ACCENT}" font-family="'Geist Mono'" font-size="10" letter-spacing="2">ONE PERSON / FULL SYSTEM</text>
{''.join(texts)}
<path d="M28 592H572" stroke="{LINE}"/>
<text x="28" y="640" fill="{FG}" font-family="'Archivo'" font-size="34">Technik, die Charakter zeigt<tspan fill="{ACCENT}">.</tspan></text>
<text x="28" y="681" fill="{MUTED}" font-family="'Manrope'" font-size="14">Founder / Developer · Structiva · Austria</text>
<circle cx="32" cy="719" r="4" fill="{ACCENT}"/>
<text x="50" y="723" fill="{MUTED}" font-family="'Geist Mono'" font-size="10" letter-spacing="1">PORTRAIT PRINTS ONCE, THEN HOLDS</text>
'''
    return svg_document(width, height, body, css)


def main() -> None:
    parser = argparse.ArgumentParser(description="Generate the animated Structiva ASCII portrait SVG.")
    parser.add_argument("--input", required=True, type=Path)
    parser.add_argument("--output", default=Path("assets/portrait.svg"), type=Path)
    parser.add_argument("--mobile-output", default=Path("assets/portrait-mobile.svg"), type=Path)
    parser.add_argument("--cols", default=104, type=int)
    args = parser.parse_args()

    image = Image.open(args.input).convert("RGB")
    rows = ascii_rows(image, args.cols)
    mobile_rows = ascii_rows(image, min(args.cols, 88))
    output = args.output if args.output.is_absolute() else Path.cwd() / args.output
    output.parent.mkdir(parents=True, exist_ok=True)
    font_dir = Path(__file__).resolve().parents[1] / "assets" / "fonts"
    output.write_text(render(rows, font_dir), encoding="utf-8")
    mobile_output = args.mobile_output if args.mobile_output.is_absolute() else Path.cwd() / args.mobile_output
    mobile_output.write_text(render_mobile(mobile_rows, font_dir), encoding="utf-8")
    print(f"wrote {output} ({len(rows)} rows × {args.cols} columns)")
    print(f"wrote {mobile_output}")


if __name__ == "__main__":
    main()
