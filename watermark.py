#!/usr/bin/env python3
"""
watermark.py
Adds www.ramkrishan.com watermark to upper-right of an image.

Usage:
    python3 watermark.py <image_path> <output_path>

Output: JSON {"success": true} or {"success": false, "error": "..."}
"""
import sys
import json
import traceback


def add_watermark(image_path: str, output_path: str) -> dict:
    from PIL import Image, ImageDraw, ImageFont

    img = Image.open(image_path).convert('RGBA')
    W, H = img.size

    watermark_text = "www.ramkrishan.com"
    font_size = max(22, int(H * 0.032))  # ~3.2% of image height

    # Try system fonts in order
    font = None
    for font_path in [
        "/System/Library/Fonts/Helvetica.ttc",
        "/System/Library/Fonts/Arial.ttf",
        "/Library/Fonts/Arial.ttf",
        "/Users/ramdudeja/Library/Fonts/NotoSansDevanagari[wdth,wght].ttf",
    ]:
        try:
            font = ImageFont.truetype(font_path, font_size)
            break
        except Exception:
            continue
    if font is None:
        font = ImageFont.load_default()

    # Measure text size
    dummy = Image.new('RGBA', (1, 1))
    d = ImageDraw.Draw(dummy)
    bbox = d.textbbox((0, 0), watermark_text, font=font)
    tw = bbox[2] - bbox[0]
    th = bbox[3] - bbox[1]

    # Position: upper-right with 16px margin
    margin = 16
    x = W - tw - margin
    y = margin

    # Draw on a transparent overlay
    overlay = Image.new('RGBA', img.size, (0, 0, 0, 0))
    draw = ImageDraw.Draw(overlay)

    # Dark shadow for readability on any background
    shadow_offset = max(2, font_size // 18)
    draw.text((x + shadow_offset, y + shadow_offset), watermark_text,
              font=font, fill=(0, 0, 0, 180))
    # White semi-transparent text
    draw.text((x, y), watermark_text, font=font, fill=(255, 255, 255, 210))

    result = Image.alpha_composite(img, overlay)
    result.convert('RGB').save(output_path, 'JPEG', quality=92)
    return {"success": True, "path": output_path}


def main():
    if len(sys.argv) < 3:
        print(json.dumps({"success": False,
                          "error": "Usage: watermark.py <image_path> <output_path>"}))
        sys.exit(1)
    try:
        result = add_watermark(sys.argv[1], sys.argv[2])
        print(json.dumps(result, ensure_ascii=False))
    except Exception as e:
        print(json.dumps({"success": False, "error": str(e),
                          "trace": traceback.format_exc()[-400:]},
                         ensure_ascii=False))


if __name__ == '__main__':
    main()
