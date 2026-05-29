"""Generate src/rtib/resources/icons/rtib.ico from scratch.

Design: rounded square in the brand blue, white "R" centred, bold sans-serif.
Multi-resolution (16, 24, 32, 48, 64, 128, 256) so Windows uses the right
size for the taskbar/explorer/start menu.

Run from the project root:
    python scripts/generate-icon.py
"""

from __future__ import annotations

import sys
from pathlib import Path

from PIL import Image, ImageDraw, ImageFont


ICON_SIZES = [16, 24, 32, 48, 64, 128, 256]
BRAND_BLUE = (37, 99, 235)  # #2563eb
TEXT_COLOR = (255, 255, 255)


def _find_bold_font(size: int) -> ImageFont.FreeTypeFont:
    """Look for a usable bold sans-serif. Fall back to PIL default."""
    candidates = [
        "C:/Windows/Fonts/segoeuib.ttf",  # Segoe UI Bold
        "C:/Windows/Fonts/seguibl.ttf",  # Segoe UI Black
        "C:/Windows/Fonts/arialbd.ttf",  # Arial Bold
        "/System/Library/Fonts/Supplemental/Arial Bold.ttf",
        "/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf",
    ]
    for candidate in candidates:
        if Path(candidate).exists():
            return ImageFont.truetype(candidate, size)
    return ImageFont.load_default()


def _render_icon(size: int) -> Image.Image:
    img = Image.new("RGBA", (size, size), (0, 0, 0, 0))
    draw = ImageDraw.Draw(img)
    # Rounded square background
    radius = max(1, size // 6)
    draw.rounded_rectangle(
        [(0, 0), (size - 1, size - 1)],
        radius=radius,
        fill=BRAND_BLUE,
    )

    # Centred "R"
    target_glyph_height = int(size * 0.70)
    font = _find_bold_font(target_glyph_height)
    text = "R"
    # textbbox gives us the rendered glyph's bounds; we use that to centre.
    bbox = draw.textbbox((0, 0), text, font=font)
    text_width = bbox[2] - bbox[0]
    text_height = bbox[3] - bbox[1]
    x = (size - text_width) // 2 - bbox[0]
    # Optical centring: shift slightly up because uppercase glyphs hang lower.
    y = (size - text_height) // 2 - bbox[1] - max(1, size // 32)
    draw.text((x, y), text, font=font, fill=TEXT_COLOR)
    return img


def main() -> int:
    project_root = Path(__file__).resolve().parent.parent
    output_dir = project_root / "src" / "rtib" / "resources" / "icons"
    output_dir.mkdir(parents=True, exist_ok=True)
    output_path = output_dir / "rtib.ico"

    images = [_render_icon(s) for s in ICON_SIZES]
    # PIL writes a multi-size .ico from the largest image plus an explicit list.
    images[-1].save(
        output_path,
        format="ICO",
        sizes=[(s, s) for s in ICON_SIZES],
        append_images=images[:-1],
    )

    # Also drop a 256px PNG next to the .ico for previewing in editors.
    images[-1].save(output_dir / "rtib-256.png", format="PNG")

    print(f"Wrote {output_path}")
    print(f"      {output_dir / 'rtib-256.png'}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
