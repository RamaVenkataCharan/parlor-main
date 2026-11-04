"""Icon Generator for Parlor Desktop Shortcuts.

Generates high-resolution, multi-size Windows icon files (.ico):
- scripts/parlor.ico: Blue/indigo gradient with modern white letter 'P'
- scripts/parlor-stop.ico: Crimson/red gradient with clean white stop square
Sizes embedded: 16x16, 32x32, 48x48, 256x256
"""

from pathlib import Path
from PIL import Image, ImageDraw, ImageFont

ROOT = Path(__file__).resolve().parent.parent
SCRIPTS_DIR = ROOT / "scripts"


def create_parlor_icon(size: int = 512) -> Image.Image:
    """Renders a modern, round blue-gradient Parlor 'P' icon."""
    img = Image.new("RGBA", (size, size), (0, 0, 0, 0))
    draw = ImageDraw.Draw(img)

    # 1. Smooth gradient circle
    # Gradient from top-left (royal blue #2563eb) to bottom-right (indigo #4f46e5)
    r = size // 2 - int(size * 0.04)
    cx, cy = size // 2, size // 2

    # High-quality supersampled circle with subtle drop shadow
    # Outer ambient shadow
    for i in range(12):
        alpha = int(18 * (1.0 - i / 12.0))
        draw.ellipse(
            [cx - r - i, cy - r - i + int(size * 0.02), cx + r + i, cy + r + i + int(size * 0.02)],
            fill=(15, 23, 42, alpha)
        )

    # Gradient fill for main circle
    # Interpolate colors vertically/diagonally
    circle_mask = Image.new("L", (size, size), 0)
    c_draw = ImageDraw.Draw(circle_mask)
    c_draw.ellipse([cx - r, cy - r, cx + r, cy + r], fill=255)

    gradient = Image.new("RGBA", (size, size))
    g_draw = ImageDraw.Draw(gradient)

    c_top = (37, 99, 235)      # #2563eb Vibrant Blue
    c_bot = (99, 102, 241)     # #6366f1 Indigo / Violet

    for y in range(size):
        ratio = y / size
        cr = int(c_top[0] * (1 - ratio) + c_bot[0] * ratio)
        cg = int(c_top[1] * (1 - ratio) + c_bot[1] * ratio)
        cb = int(c_top[2] * (1 - ratio) + c_bot[2] * ratio)
        g_draw.line([(0, y), (size, y)], fill=(cr, cg, cb, 255))

    img.paste(gradient, (0, 0), circle_mask)

    # Subtle inner border / highlight
    b_draw = ImageDraw.Draw(img)
    b_draw.ellipse([cx - r, cy - r, cx + r, cy + r], outline=(255, 255, 255, 60), width=max(2, int(size * 0.012)))

    # Draw modern, bold letter 'P'
    # Try loading Windows system font 'Segoe UI', 'Arial Bold', or draw geometric glyph
    font_loaded = False
    for font_name in ["segoeuib.ttf", "arialbd.ttf", "Calibri-Bold.ttf"]:
        try:
            font = ImageFont.truetype(font_name, int(size * 0.58))
            font_loaded = True
            break
        except Exception:
            continue

    if font_loaded:
        # Get bounding box to center perfectly
        bbox = draw.textbbox((0, 0), "P", font=font)
        text_w = bbox[2] - bbox[0]
        text_h = bbox[3] - bbox[1]
        # Slight optical offset for 'P' (P has more weight on top-left)
        tx = cx - text_w // 2 - int(size * 0.02)
        ty = cy - text_h // 2 - int(size * 0.05)
        # Subtle text shadow
        draw.text((tx, ty + int(size * 0.015)), "P", fill=(15, 23, 42, 60), font=font)
        # Crisp white text
        draw.text((tx, ty), "P", fill=(255, 255, 255, 255), font=font)
    else:
        # Geometric fallback for 'P'
        stem_x = int(cx - size * 0.22)
        stem_y0 = int(cy - size * 0.28)
        stem_y1 = int(cy + size * 0.28)
        stem_w = int(size * 0.12)
        draw.rectangle([stem_x, stem_y0, stem_x + stem_w, stem_y1], fill=(255, 255, 255, 255))
        loop_r = int(size * 0.22)
        loop_cy = int(stem_y0 + loop_r)
        draw.ellipse([stem_x, stem_y0, stem_x + loop_r * 2, stem_y0 + loop_r * 2], fill=(255, 255, 255, 255))
        draw.ellipse([stem_x + stem_w, stem_y0 + stem_w, stem_x + loop_r * 2 - stem_w, stem_y0 + loop_r * 2 - stem_w], fill=c_top)

    return img


def create_stop_icon(size: int = 512) -> Image.Image:
    """Renders a round crimson-gradient Stop Parlor icon with a white square."""
    img = Image.new("RGBA", (size, size), (0, 0, 0, 0))
    draw = ImageDraw.Draw(img)

    r = size // 2 - int(size * 0.04)
    cx, cy = size // 2, size // 2

    for i in range(12):
        alpha = int(18 * (1.0 - i / 12.0))
        draw.ellipse(
            [cx - r - i, cy - r - i + int(size * 0.02), cx + r + i, cy + r + i + int(size * 0.02)],
            fill=(15, 23, 42, alpha)
        )

    circle_mask = Image.new("L", (size, size), 0)
    c_draw = ImageDraw.Draw(circle_mask)
    c_draw.ellipse([cx - r, cy - r, cx + r, cy + r], fill=255)

    gradient = Image.new("RGBA", (size, size))
    g_draw = ImageDraw.Draw(gradient)

    c_top = (220, 38, 38)     # #dc2626 Red
    c_bot = (153, 27, 27)     # #991b1b Crimson

    for y in range(size):
        ratio = y / size
        cr = int(c_top[0] * (1 - ratio) + c_bot[0] * ratio)
        cg = int(c_top[1] * (1 - ratio) + c_bot[1] * ratio)
        cb = int(c_top[2] * (1 - ratio) + c_bot[2] * ratio)
        g_draw.line([(0, y), (size, y)], fill=(cr, cg, cb, 255))

    img.paste(gradient, (0, 0), circle_mask)

    b_draw = ImageDraw.Draw(img)
    b_draw.ellipse([cx - r, cy - r, cx + r, cy + r], outline=(255, 255, 255, 60), width=max(2, int(size * 0.012)))

    # Centered stop square with rounded corners
    sq_size = int(size * 0.38)
    sq_x0 = cx - sq_size // 2
    sq_y0 = cy - sq_size // 2
    sq_x1 = sq_x0 + sq_size
    sq_y1 = sq_y0 + sq_size
    corner_r = int(sq_size * 0.18)

    # Shadow
    b_draw.rounded_rectangle([sq_x0, sq_y0 + int(size * 0.015), sq_x1, sq_y1 + int(size * 0.015)],
                             radius=corner_r, fill=(15, 23, 42, 60))
    # Crisp white square
    b_draw.rounded_rectangle([sq_x0, sq_y0, sq_x1, sq_y1], radius=corner_r, fill=(255, 255, 255, 255))

    return img


def main():
    sizes = [(16, 16), (32, 32), (48, 48), (256, 256)]

    parlor_img = create_parlor_icon(512)
    parlor_ico_path = SCRIPTS_DIR / "parlor.ico"
    parlor_img.save(parlor_ico_path, format="ICO", sizes=sizes)
    print(f"Generated Parlor launcher icon: {parlor_ico_path} ({sizes})")

    stop_img = create_stop_icon(512)
    stop_ico_path = SCRIPTS_DIR / "parlor-stop.ico"
    stop_img.save(stop_ico_path, format="ICO", sizes=sizes)
    print(f"Generated Stop Parlor icon: {stop_ico_path} ({sizes})")


if __name__ == "__main__":
    main()
