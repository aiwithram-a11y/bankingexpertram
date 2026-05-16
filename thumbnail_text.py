#!/usr/bin/env python3
"""
thumbnail_text.py
Adds a YouTube-style Hindi title overlay to a thumbnail image.

Uses HarfBuzz for proper Devanagari text shaping (correct choti-e-matra
placement) and FreeType for glyph rendering. No dependency on Pango or
ImageMagick text engine.

Usage:
    python3 thumbnail_text.py <image_path> <title_text> <output_path>

Output: JSON {"success": true, "path": "...", "lines": N}
"""
import sys
import json
import textwrap
import traceback
import numpy as np

FONT_PATH = '/Users/ramdudeja/Library/Fonts/NotoSansDevanagari[wdth,wght].ttf'


def hex_to_rgb(h):
    h = h.lstrip('#')
    return tuple(int(h[i:i+2], 16) for i in (0, 2, 4))


def render_line_harfbuzz(text: str, font_path: str, font_size_px: int):
    """
    Shape text with HarfBuzz → render shaped glyphs with FreeType.
    HarfBuzz applies OpenType GSUB rules: ि is correctly placed BEFORE
    the consonant in the output glyph stream, regardless of Unicode order.

    Returns (numpy RGBA uint8 array, pixel_width)
    """
    import uharfbuzz as hb
    import freetype

    with open(font_path, 'rb') as f:
        font_data = f.read()

    # ── HarfBuzz setup ──────────────────────────────────────────────────
    hb_face = hb.Face(font_data)
    hb_font = hb.Font(hb_face)
    upem    = hb_face.upem              # units per em (usually 1000 or 2048)

    # Scale: use upem so HarfBuzz positions are in font design units.
    # We convert to pixels using ppu = font_size_px / upem.
    hb_font.scale = (upem, upem)

    buf = hb.Buffer()
    buf.add_str(text)
    buf.guess_segment_properties()     # auto-detects Devanagari script
    hb.shape(hb_font, buf)             # applies GSUB/GPOS — reorders ि correctly

    infos     = buf.glyph_infos        # glyph_infos[i].codepoint = GLYPH INDEX
    positions = buf.glyph_positions    # advances/offsets in font design units

    ppu = font_size_px / upem          # pixels per unit

    # ── FreeType setup ──────────────────────────────────────────────────
    ft_face = freetype.Face(font_path)
    ft_face.set_pixel_sizes(0, font_size_px)

    ascender  = ft_face.size.ascender  >> 6
    descender = -(ft_face.size.descender >> 6)
    line_h    = ascender + descender + 4

    total_px = int(sum(p.x_advance * ppu for p in positions)) + font_size_px
    canvas   = np.zeros((line_h, max(total_px, 1), 4), dtype=np.uint8)

    cursor_x  = 0
    baseline_y = ascender + 2

    for info, pos in zip(infos, positions):
        glyph_idx = info.codepoint     # shaped glyph index — NOT Unicode codepoint

        gx = cursor_x + int(pos.x_offset * ppu)
        gy = baseline_y - int(pos.y_offset * ppu)

        # Render glyph by INDEX — this is what makes Devanagari correct.
        # HarfBuzz has already done the reordering; we just paint each glyph.
        ft_face.load_glyph(glyph_idx, freetype.FT_LOAD_RENDER)
        bm = ft_face.glyph.bitmap

        if bm.width > 0 and bm.rows > 0:
            x0 = gx + ft_face.glyph.bitmap_left
            y0 = gy - ft_face.glyph.bitmap_top
            x1, y1 = x0 + bm.width, y0 + bm.rows
            H, W = canvas.shape[:2]

            cx0, cy0 = max(0, x0), max(0, y0)
            cx1, cy1 = min(W, x1), min(H, y1)

            if cx1 > cx0 and cy1 > cy0:
                bm_arr = np.frombuffer(bytes(bm.buffer), dtype=np.uint8)
                bm_arr = bm_arr.reshape(bm.rows, bm.width)
                src    = bm_arr[cy0 - y0: cy1 - y0, cx0 - x0: cx1 - x0]
                canvas[cy0:cy1, cx0:cx1, 3] = np.maximum(
                    canvas[cy0:cy1, cx0:cx1, 3], src
                )

        cursor_x += int(pos.x_advance * ppu)

    return canvas, cursor_x


def make_outline_alpha(alpha: np.ndarray, width: int) -> np.ndarray:
    """Dilate the alpha mask to create an outline layer."""
    from PIL import Image, ImageFilter
    img = Image.fromarray(alpha, mode='L')
    for _ in range(width):
        img = img.filter(ImageFilter.MaxFilter(3))
    return np.array(img)


def colorize(canvas: np.ndarray, fill_rgb: tuple, outline_rgb: tuple,
             outline_width: int) -> 'PIL.Image.Image':
    from PIL import Image
    alpha    = canvas[:, :, 3]
    out_alph = make_outline_alpha(alpha, outline_width)

    H, W = alpha.shape
    result = np.zeros((H, W, 4), dtype=np.uint8)

    # Outline layer
    result[:, :, 0] = outline_rgb[0]
    result[:, :, 1] = outline_rgb[1]
    result[:, :, 2] = outline_rgb[2]
    result[:, :, 3] = out_alph

    # Fill layer on top
    mask = alpha > 0
    result[mask, 0] = fill_rgb[0]
    result[mask, 1] = fill_rgb[1]
    result[mask, 2] = fill_rgb[2]
    result[mask, 3] = alpha[mask]

    return Image.fromarray(result, 'RGBA')


def add_thumbnail_text(image_path: str, title: str, output_path: str) -> dict:
    from PIL import Image, ImageDraw

    img = Image.open(image_path).convert('RGB')
    W, H = img.size

    title = title.replace('#', '').strip()
    if len(title) > 130:
        title = title[:127] + '...'

    lines = textwrap.wrap(title, width=22)
    if not lines:
        lines = [title]

    font_size  = 72 if len(lines) <= 2 else (60 if len(lines) == 3 else 50)
    line_gap   = 12
    outline_w  = 5
    fill_colors   = ['#FFE000', '#FFFFFF']
    outline_color = '#000000'

    # ── Render each line with HarfBuzz + FreeType ──────────────────────
    rendered = []
    for line in lines:
        canvas, px_w = render_line_harfbuzz(line, FONT_PATH, font_size)
        line_img = colorize(canvas, hex_to_rgb(fill_colors[len(rendered) % 2]),
                            hex_to_rgb(outline_color), outline_w)
        rendered.append(line_img)

    # ── Calculate bar height ────────────────────────────────────────────
    total_text_h = sum(r.height for r in rendered) + line_gap * (len(rendered) - 1)
    bar_h = total_text_h + 48

    # ── Dark gradient bar at bottom of base image ───────────────────────
    overlay = Image.new('RGBA', img.size, (0, 0, 0, 0))
    ov_draw = ImageDraw.Draw(overlay)
    bar_top = H - bar_h - 6
    for y in range(bar_top, H):
        alpha = int(220 * (y - bar_top) / (H - bar_top))
        ov_draw.line([(0, y), (W, y)], fill=(0, 0, 0, alpha))
    img = Image.alpha_composite(img.convert('RGBA'), overlay).convert('RGBA')

    # ── Paste each rendered line onto the image ─────────────────────────
    y_cursor = H - bar_h + 16
    for line_img in rendered:
        lw, lh = line_img.size
        x = max(16, (W - lw) // 2)
        img.paste(line_img, (x, y_cursor), line_img)
        y_cursor += lh + line_gap

    img.convert('RGB').save(output_path, 'JPEG', quality=92)
    return {"success": True, "path": output_path, "lines": len(lines)}


def main():
    if len(sys.argv) < 4:
        print(json.dumps({"success": False,
                          "error": "Usage: thumbnail_text.py <image_path> <title> <output_path>"}))
        sys.exit(1)

    try:
        result = add_thumbnail_text(sys.argv[1], sys.argv[2], sys.argv[3])
        print(json.dumps(result, ensure_ascii=False))
    except Exception as e:
        print(json.dumps({"success": False, "error": str(e),
                          "trace": traceback.format_exc()[-500:]},
                         ensure_ascii=False))


if __name__ == '__main__':
    main()
