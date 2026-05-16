#!/usr/bin/env python3
"""
Hindi Video Generator V15 - Multi-Image Background Support
===========================================================
Each paragraph (section) in the script gets its own background image
according to a configurable mapping. Falls back to image0 for any
paragraph beyond the explicit mapping.

Image naming convention : image{N}.jpeg
Base path               : /Users/ramdudeja/Desktop/bankingexpertram

Paragraph → image mapping
--------------------------
Loaded exclusively from script_editor.xlsx (columns A=paragraph, B=image number).
Place script_editor.xlsx in the same folder as this script, or pass --image-map.
Any image numbers present in column B are valid — no fixed count required.
Paragraphs beyond the map → image0 (fallback).

Usage:
    python3 generate_video.py --article script.md --output-dir output_v16
"""

import argparse
import hashlib
import base64
import os
import re
import subprocess
import tempfile
import textwrap
from pathlib import Path
from typing import Optional, List
from PIL import Image

# ── Config ─────────────────────────────────────────────────────────────────────
VIDEO_W, VIDEO_H = 1920, 1080
FPS = 30
WATERMARK = "ramkrishan.com"
TTS_VOICE = "Tara"
TTS_RATE = 158
CRF = 20

# ── Multi-Image Config ─────────────────────────────────────────────────────────
IMAGE_BASE_DIR = "/Users/ramdudeja/Desktop/bankingexpertram_abacus/images"

# Default empty map — populated at runtime from --image-map JSON.
PARA_TO_IMAGE_MAP: dict = {}
FALLBACK_IMAGE_NUM = 0


def load_image_map_from_excel(excel_path: str) -> dict:
    """
    Load para_to_image_map from script_editor.xlsx.

    Sheet   : 'Script Editor'
    Row 1-3 : titles / header — skipped (header row is row 3, index 2)
    Col A   : script text (ignored here)
    Col B   : image number  (the N in imageN.jpeg)
    Col C   : para label e.g. 'Para 1', 'Para 2', …  → used for 0-based index

    Returns dict {para_idx_0based: image_num}
    """
    try:
        import pandas as pd
    except ImportError:
        raise ImportError("pandas is required for Excel support — run: pip install pandas openpyxl")

    df = pd.read_excel(
        excel_path,
        sheet_name="Script Editor",
        engine="openpyxl",
        header=2,          # row 3 (0-indexed row 2) is the header row
        usecols="B,C",     # Col B = image number, Col C = para label
    )

    # Normalise column names
    df.columns = [str(c).strip() for c in df.columns]
    img_col  = df.columns[0]   # 'Image No.  ▼ (0–9)' or similar
    para_col = df.columns[1]   # 'Para #' or similar

    # Drop rows where either value is missing
    df = df[[img_col, para_col]].dropna()

    # Extract integer para index from labels like 'Para 1', 'Para 2', …
    def parse_para(val):
        s = str(val).strip()
        # Try direct int first ('1', '2', …)
        try:
            return int(s)
        except ValueError:
            pass
        # Extract trailing number from 'Para N'
        import re
        m = re.search(r'(\d+)$', s)
        if m:
            return int(m.group(1))
        raise ValueError(f"Cannot parse para index from: {val!r}")

    df["_para_idx"] = df[para_col].apply(parse_para)
    df["_img_num"]  = df[img_col].astype(int)

    # Convert 1-based para numbers to 0-based
    min_para = int(df["_para_idx"].min())
    offset   = 1 if min_para == 1 else 0

    result = {int(row["_para_idx"]) - offset: int(row["_img_num"])
              for _, row in df.iterrows()}

    max_img = max(result.values()) if result else 0
    print(f"  [EXCEL] Loaded {len(result)} para→image entries | max image number: {max_img}")
    return result


def resolve_image_file(image_num: int) -> Optional[str]:
    """
    Find the actual file for image{N} in IMAGE_BASE_DIR.
    Matches 'image{N}.jpeg', 'image{N}.jpg', or dated 'image{N}_*.jpeg/jpg'.
    Returns full path string, or None if not found.
    """
    base = Path(IMAGE_BASE_DIR)
    for ext in ("jpeg", "jpg"):
        exact = base / f"image{image_num}.{ext}"
        if exact.exists():
            return str(exact)
        matches = sorted(base.glob(f"image{image_num}_*.{ext}"))
        if matches:
            return str(matches[-1])
    return None


def _resolve_image_num(para_idx: int) -> int:
    """Return the image number for para_idx, cycling through 0…max_img for unmapped paragraphs."""
    if para_idx in PARA_TO_IMAGE_MAP:
        return PARA_TO_IMAGE_MAP[para_idx]
    if PARA_TO_IMAGE_MAP:
        max_img = max(PARA_TO_IMAGE_MAP.values())
        return para_idx % (max_img + 1)
    return FALLBACK_IMAGE_NUM


def get_image_for_paragraph(para_idx: int) -> str:
    """
    Return full path to background image for given paragraph.

    If para_idx is in PARA_TO_IMAGE_MAP, use that mapping directly.
    Otherwise cycle through image0…imageN (N = max mapped image number)
    so every paragraph gets a meaningful background instead of always
    falling back to image0.
    """
    image_num = _resolve_image_num(para_idx)

    path = resolve_image_file(image_num)
    if path is None:
        path = resolve_image_file(FALLBACK_IMAGE_NUM)
    if path is None:
        return str(Path(IMAGE_BASE_DIR) / f"image{image_num}.jpeg")
    return path


def verify_images() -> List[str]:
    """Check which image files exist. Returns list of warning strings (empty = all good)."""
    warnings = []
    needed = set(PARA_TO_IMAGE_MAP.values()) | {FALLBACK_IMAGE_NUM}
    for n in sorted(needed):
        if resolve_image_file(n) is None:
            warnings.append(f"  [WARN] Missing image{n} (no image{n}.jpeg/.jpg or image{n}_*.jpeg in {IMAGE_BASE_DIR})")
    return warnings


# ── Legacy single-image default (kept for --bg-image CLI override) ─────────────
DEFAULT_BG_IMAGE = "/Users/ramdudeja/Desktop/Hindi-video-generator/image_rk_url.jpg"

# Set to True here to hard-code single-image mode without using the CLI flag.
# Can also be activated at runtime with --single-image or --bg-image.
USE_SINGLE_BG: bool = False

# Python renderer fonts
HINDI_FONT_PATHS = [
    "/Users/ramdudeja/Desktop/Hindi-video-generator/fonts/NotoSansDevanagari-Regular.ttf",
    "/System/Library/Fonts/Supplemental/DevanagariMT.ttc",
    "/System/Library/Fonts/Kohinoor.ttc",
    "/Library/Fonts/NotoSansDevanagari-Regular.ttf",
    "/System/Library/Fonts/Supplemental/Arial Unicode.ttf",
]

BROAD_FONT_PATHS = [
    "/System/Library/Fonts/Supplemental/Arial Unicode.ttf",
    "/System/Library/Fonts/Kohinoor.ttc",
    "/System/Library/Fonts/Supplemental/DevanagariMT.ttc",
    "/Users/ramdudeja/Desktop/Hindi-video-generator/fonts/NotoSansDevanagari-Regular.ttf",
    "/Library/Fonts/NotoSansDevanagari-Regular.ttf",
]

# ── CLI ───────────────────────────────────────────────────────────────────────
def parse_args():
    p = argparse.ArgumentParser(description="Hindi Video Generator V15 - Multi-Image")
    p.add_argument("--article",    default=None)
    p.add_argument("--output-dir", default=None)
    p.add_argument("--bg-image",   default=None,
                   help="Override ALL backgrounds with a single image (disables multi-image mode)")
    p.add_argument("--no-sarvam",  action="store_true", help="Use macOS say instead of Sarvam")
    p.add_argument("--crf",        type=int, default=20, help="CRF value")
    p.add_argument("--short",      action="store_true",  help="Short version (2 sentences/section)")
    p.add_argument("--clean-clips", action="store_true",
                   help="Delete clips/ and text_images/ before running (keeps audio/). "
                        "Use this whenever background images change.")
    p.add_argument("--single-image", action="store_true",
                   help="Use one background image for ALL clips (like V13 behaviour). "
                        "Uses DEFAULT_BG_IMAGE unless --bg-image is also set.")
    p.add_argument("--image-map", default=None,
                   help="Path to script_editor.xlsx. Overrides auto-detected file next to script.")
    return p.parse_args()


ARGS = parse_args()

SCRIPT_DIR  = Path(__file__).parent
ARTICLE_FILE = ARGS.article if ARGS.article else SCRIPT_DIR / "script.md"
OUTPUT_DIR   = Path(ARGS.output_dir) if ARGS.output_dir else SCRIPT_DIR / "output_v19"
AUDIO_DIR    = OUTPUT_DIR / "audio"
TEXT_IMG_DIR = OUTPUT_DIR / "text_images"
FINAL_VIDEO  = OUTPUT_DIR / "final_video.mp4"

CRF = ARGS.crf
MAX_SENTENCES_SHORT = 2

# Sarvam TTS config
SARVAM_API_KEY  = "sk_3rguk1va_YWUseNZY9XeLLRzSuOTzwyAa"
SARVAM_TTS_URL  = "https://api.sarvam.ai/text-to-speech/stream"


def ensure_dirs():
    """Create output directories. If --clean-clips, wipe text_images, frames, and segments first."""
    import shutil
    if ARGS.clean_clips:
        for d in [TEXT_IMG_DIR, OUTPUT_DIR / "segments"]:
            if d.exists():
                shutil.rmtree(d)
                print(f"  [CLEAN] Removed {d}")
        for pattern in ["frame_*.png", "master_audio*.wav", "frames_list.txt",
                        "segments_list.txt", "silent_video.mp4", "seg_*.mp4"]:
            for f in OUTPUT_DIR.glob(pattern):
                f.unlink()
    for d in [OUTPUT_DIR, AUDIO_DIR, TEXT_IMG_DIR]:
        d.mkdir(parents=True, exist_ok=True)


# ── Font helpers ───────────────────────────────────────────────────────────────
def _get_hindi_font(size: int):
    from PIL import ImageFont
    for path in BROAD_FONT_PATHS:
        if os.path.exists(path):
            try:
                return ImageFont.truetype(path, size)
            except Exception:
                continue
    return ImageFont.load_default()


def _scaled_font_size(text: str, base: int) -> int:
    n = len(text)
    if n > 80: return 32
    if n > 60: return 36
    if n > 40: return 40
    return base


# ── Text Renderers ─────────────────────────────────────────────────────────────
def _render_with_playwright(text: str, output_path: str, font_size: int) -> bool:
    try:
        from playwright.sync_api import sync_playwright
    except ImportError:
        print("  [INFO] Playwright not installed — run: pip install playwright && playwright install chromium")
        return False

    fs = _scaled_font_size(text, font_size)

    hindi_font_uri = ""
    for fp in HINDI_FONT_PATHS:
        if os.path.exists(fp):
            hindi_font_uri = Path(fp).as_uri()
            break

    font_face_rule = (
        f"@font-face {{ font-family: 'DevFont'; src: url('{hindi_font_uri}'); }}"
        if hindi_font_uri else ""
    )
    font_family = (
        "'DevFont', 'Noto Sans Devanagari', 'Kohinoor Devanagari', "
        "'DevanagariMT', 'Arial Unicode MS', 'Noto Sans', sans-serif"
    )

    import html as _html
    safe_text = _html.escape(text)

    html_content = f"""<!DOCTYPE html>
<html>
<head>
<meta charset="UTF-8">
<style>
  * {{ margin: 0; padding: 0; box-sizing: border-box; }}
  html, body {{
    width: {VIDEO_W}px;
    height: {VIDEO_H}px;
    background: transparent;
    overflow: hidden;
  }}
  {font_face_rule}
  .box {{
    position: absolute;
    bottom: 80px;
    left: 50%;
    transform: translateX(-50%);
    max-width: 84%;
    background: rgba(0, 0, 0, 0.78);
    border-radius: 12px;
    padding: 22px 52px;
    text-align: center;
    word-wrap: break-word;
  }}
  .text {{
    font-family: {font_family};
    font-size: {fs}px;
    color: #ffffff;
    line-height: 1.6;
    text-shadow: 2px 2px 4px rgba(0,0,0,0.9), -1px -1px 3px rgba(0,0,0,0.7);
  }}
  .watermark {{
    position: absolute;
    bottom: 28px;
    right: 32px;
    font-family: Arial, sans-serif;
    font-size: 18px;
    color: rgba(180, 180, 180, 0.7);
  }}
</style>
</head>
<body>
  <div class="box"><div class="text">{safe_text}</div></div>
  <div class="watermark">{WATERMARK}</div>
</body>
</html>"""

    try:
        Path(output_path).parent.mkdir(parents=True, exist_ok=True)
        with sync_playwright() as p:
            browser = p.chromium.launch()
            page = browser.new_page(viewport={"width": VIDEO_W, "height": VIDEO_H})
            page.set_content(html_content, wait_until="domcontentloaded")
            page.screenshot(path=str(output_path), type="png",
                            omit_background=True, full_page=False)
            browser.close()
        return True
    except Exception as e:
        print(f"  [PLAYWRIGHT ERROR] {e}")
        return False


def _render_with_pillow(text: str, output_path: str, font_size: int) -> bool:
    from PIL import ImageDraw, ImageFont

    fs = _scaled_font_size(text, font_size)

    try:
        Path(output_path).parent.mkdir(parents=True, exist_ok=True)
        img  = Image.new("RGBA", (VIDEO_W, VIDEO_H), (0, 0, 0, 0))
        draw = ImageDraw.Draw(img)
        font = _get_hindi_font(fs)

        chars_per_line = max(20, int(VIDEO_W * 0.80 / (fs * 0.55)))
        lines = textwrap.wrap(text, width=chars_per_line) or [text]

        line_height  = int(fs * 1.55)
        total_text_h = len(lines) * line_height
        pad_x, pad_y = 60, 20

        max_line_w = max(
            (draw.textbbox((0, 0), ln, font=font)[2] - draw.textbbox((0, 0), ln, font=font)[0])
            for ln in lines
        )
        box_w = min(max_line_w + pad_x * 2, VIDEO_W - 40)
        box_h = total_text_h + pad_y * 2
        box_x = (VIDEO_W - box_w) // 2
        box_y = VIDEO_H - box_h - 80

        overlay = Image.new("RGBA", (VIDEO_W, VIDEO_H), (0, 0, 0, 0))
        ImageDraw.Draw(overlay).rounded_rectangle(
            [box_x, box_y, box_x + box_w, box_y + box_h],
            radius=12, fill=(0, 0, 0, 190)
        )
        img  = Image.alpha_composite(img, overlay)
        draw = ImageDraw.Draw(img)

        y = box_y + pad_y
        for line in lines:
            bb = draw.textbbox((0, 0), line, font=font)
            x  = (VIDEO_W - (bb[2] - bb[0])) // 2
            draw.text((x + 2, y + 2), line, font=font, fill=(0, 0, 0, 200))
            draw.text((x, y),          line, font=font, fill=(255, 255, 255, 255))
            y += line_height

        wm_font = _get_hindi_font(18)
        draw.text((VIDEO_W - 200, VIDEO_H - 46), WATERMARK,
                  font=wm_font, fill=(150, 150, 150, 178))

        img.save(str(output_path), "PNG")
        return True

    except Exception as e:
        print(f"  [PILLOW RENDER ERROR] {e}")
        return False


def render_text_with_chrome(text: str, output_path: str, font_size: int = 44) -> bool:
    if _render_with_playwright(text, output_path, font_size):
        return True
    return _render_with_pillow(text, output_path, font_size)


# ── Background Image helpers ───────────────────────────────────────────────────
def load_and_prepare_bg_image(image_path: str) -> Optional[Image.Image]:
    """
    Load and scale+crop an image to EXACTLY VIDEO_W x VIDEO_H.

    Uses scale-to-fill (cover): scales so the image fully covers the canvas,
    then centre-crops. A final resize guarantees pixel-perfect dimensions
    regardless of floating-point rounding in intermediate steps.
    """
    try:
        img = Image.open(image_path).convert("RGB")
    except Exception as e:
        print(f"  [BG LOAD ERROR] {image_path}: {e}")
        return None

    orig_w, orig_h = img.size
    # Scale factor: cover the canvas (no letterboxing)
    scale = max(VIDEO_W / orig_w, VIDEO_H / orig_h)
    new_w = int(orig_w * scale)
    new_h = int(orig_h * scale)
    img   = img.resize((new_w, new_h), Image.LANCZOS)

    # Centre-crop to exact target size
    left = (new_w - VIDEO_W) // 2
    top  = (new_h - VIDEO_H) // 2
    img  = img.crop((left, top, left + VIDEO_W, top + VIDEO_H))

    # Hard guarantee: absorb any +/-1 px rounding from int() above
    if img.size != (VIDEO_W, VIDEO_H):
        img = img.resize((VIDEO_W, VIDEO_H), Image.LANCZOS)

    return img


def create_base_background() -> Image.Image:
    """Solid dark-blue fallback background."""
    return Image.new("RGB", (VIDEO_W, VIDEO_H), (15, 20, 45))


# ── Image cache  (avoids re-loading the same file repeatedly) ─────────────────
_bg_cache: dict = {}


def get_bg_image(image_path: str) -> Optional[Image.Image]:
    """Return a cached + prepared background image. Never caches failures."""
    if image_path not in _bg_cache:
        result = load_and_prepare_bg_image(image_path)
        if result is not None:
            _bg_cache[image_path] = result
        else:
            return None          # do NOT cache None — let caller retry / fallback
    return _bg_cache[image_path]


# ── Article parsing ─────────────────────────────────────────────────────────────
def parse_sections(filepath):
    """
    Parse script.md into sections (paragraphs).

    Two modes — auto-detected:
    1. HEADING mode  : file contains one or more lines starting with #
                       Each # line starts a new section (original behaviour).
    2. BLANK-LINE mode: no # headings found
                       Each blank-line-separated block becomes one section,
                       titled "Para 1", "Para 2", … automatically.
    """
    with open(filepath, encoding="utf-8") as f:
        raw = f.read()

    has_headings = any(line.lstrip().startswith('#') for line in raw.splitlines())

    sections = []

    if has_headings:
        # ── Original heading-based split ──────────────────────────────────────
        lines         = raw.split('\n')
        current_title = None
        current_body  = []

        for line in lines:
            line = line.strip()
            if not line:
                continue
            if line.startswith('#'):
                if current_title:
                    body = ' '.join(current_body).strip()
                    if body:
                        sections.append({"title": current_title, "body": body})
                current_title = re.sub(r'^#+\s*', '', line).strip()
                current_body  = []
            else:
                if current_title is None:
                    current_title = "Introduction"
                current_body.append(line)

        if current_title and current_body:
            body = ' '.join(current_body).strip()
            if body:
                sections.append({"title": current_title, "body": body})

    else:
        # ── Blank-line-separated paragraph split ──────────────────────────────
        # Split on one or more consecutive blank lines
        blocks = re.split(r'\n\s*\n', raw.strip())
        para_num = 1
        for block in blocks:
            body = ' '.join(line.strip() for line in block.splitlines() if line.strip())
            if body:
                sections.append({"title": f"Para {para_num}", "body": body})
                para_num += 1

    return sections


def split_sentences(text):
    """Split on Devanagari danda (।), English full-stop (.), ?, or !.
    Avoids splitting on decimal numbers (3.14) and common abbreviations.
    Caps each chunk at 450 chars so Sarvam bulbul:v3 never gets overloaded.
    """
    # Step 1: unify sentence-ending punctuation
    # Split on: ।  OR  ?  OR  !  OR  a '.' that is:
    #   - preceded by a non-digit (avoids 3.14)
    #   - NOT followed by a single uppercase letter + '.' (avoids A.I., U.S.)
    #   - followed by whitespace or end-of-string
    parts = re.split(r'(?<=[।?!])\s+|(?<=\D)\.(?!\s*[A-Z]\.)\s+', text)
    sentences = [p.strip() for p in parts if p.strip() and len(p.strip()) >= 4]

    # Step 2: hard-cap at 450 chars (Sarvam bulbul:v3 prosody limit)
    capped = []
    for s in sentences:
        while len(s) > 450:
            # break at last space before 450
            cut = s.rfind(' ', 0, 450)
            if cut == -1:
                cut = 450
            capped.append(s[:cut].strip())
            s = s[cut:].strip()
        if s:
            capped.append(s)
    return capped


# ── Voice check ─────────────────────────────────────────────────────────────────
def check_voice():
    global TTS_VOICE
    result    = subprocess.run(["say", "-v", "?"], capture_output=True, text=True)
    available = result.stdout.lower()
    if TTS_VOICE.lower() in available:
        print(f"  [VOICE] '{TTS_VOICE}' found")
        return True
    if "lekha" in available:
        TTS_VOICE = "Lekha"
        print(f"  [VOICE] Falling back to 'Lekha'")
        return True
    print("  [VOICE] No Hindi voice found, using default")
    return False


# ── TTS ─────────────────────────────────────────────────────────────────────────
def generate_audio_sarvam(text: str, output_path: str) -> float:
    import requests

    for attempt in range(3):
        try:
            response = requests.post(
                SARVAM_TTS_URL,
                headers={
                    "api-subscription-key": SARVAM_API_KEY,
                    "Content-Type": "application/json"
                },
                json={
                    "text": text,
                    "target_language_code": "hi-IN",
                    "speaker": "shubh",
                    "model": "bulbul:v3",
                    "pace": 1.0,
                    "speech_sample_rate": 22050,
                    "output_audio_codec": "mp3",
                    "enable_preprocessing": True
                },
                timeout=120
            )
            if response.status_code == 200:
                # Write to a temp file first; rename atomically only when complete.
                # Prevents a truncated MP3 from being cached as valid.
                tmp_path = output_path + ".part"
                with open(tmp_path, "wb") as f:
                    for chunk in response.iter_content(chunk_size=8192):
                        if chunk:
                            f.write(chunk)
                # Sanity check: a valid MP3 is always > 1 KB
                if os.path.getsize(tmp_path) < 1024:
                    os.remove(tmp_path)
                    print(f"    [SARVAM] Response too small — retrying")
                    continue
                os.replace(tmp_path, output_path)
                dur = get_duration(output_path)
                print(f"    [SARVAM] {dur:.1f}s")
                return dur
            else:
                print(f"    [SARVAM] Error {response.status_code}")
        except Exception as e:
            print(f"    [SARVAM] Attempt {attempt+1}: {e}")

    return generate_audio_macos(text, output_path)


def generate_audio_macos(text: str, output_path: str) -> float:
    audio_dir = Path(output_path).parent.resolve()
    audio_dir.mkdir(parents=True, exist_ok=True)

    stem = Path(output_path).stem
    aiff = audio_dir / f"temp_{stem}.aiff"
    txt  = audio_dir / f"temp_{stem}.txt"
    txt.write_text(text, encoding="utf-8")

    try:
        subprocess.run(
            ["say", "-r", str(TTS_RATE), "-o", str(aiff), "-f", str(txt), "-v", TTS_VOICE],
            check=True, capture_output=True
        )
        subprocess.run(
            ["ffmpeg", "-y", "-i", str(aiff),
             "-c:a", "aac", "-b:a", "192k", "-ar", "48000", "-ac", "2", str(output_path)],
            check=True, capture_output=True
        )
        aiff.unlink(missing_ok=True)
        txt.unlink(missing_ok=True)
        return get_duration(output_path)
    except Exception as e:
        print(f"    [MACOS TTS] Error: {e}")
        return 3.0


def generate_audio(text: str, idx: int, use_sarvam: bool = True):
    text_hash = hashlib.md5(text.encode()).hexdigest()[:8]
    mp3_path = AUDIO_DIR / f"audio_{idx:04d}_{text_hash}.mp3"
    if mp3_path.exists():
        return mp3_path, get_duration(mp3_path)
    if use_sarvam and not ARGS.no_sarvam:
        dur = generate_audio_sarvam(text, str(mp3_path))
    else:
        dur = generate_audio_macos(text, str(mp3_path))
    return mp3_path, dur


def get_duration(path) -> float:
    if not path or not Path(path).exists():
        return 3.0
    result = subprocess.run(
        ["ffprobe", "-v", "error", "-show_entries", "format=duration",
         "-of", "default=noprint_wrappers=1:nokey=1", str(path)],
        capture_output=True, text=True
    )
    try:
        return float(result.stdout.strip())
    except:
        return 3.0


# ── Frame composer (NO per-clip audio encode) ─────────────────────────────────
def compose_frame(
    bg_image_path: str,
    text: str,
    idx: int,
) -> Optional[Path]:
    """
    Render ONLY the subtitle overlay PNG (RGBA, transparent background).
    The background image is composited by FFmpeg in assemble_video so that
    every segment always reads the live image file at its true resolution —
    no PIL background caching, no stale composites, no size drift.
    Returns the text-overlay PNG path (used by assemble_video).
    """
    text_hash = hashlib.md5(text.encode()).hexdigest()[:8]

    text_img_path = TEXT_IMG_DIR / f"text_{idx:04d}_{text_hash}.png"
    if not text_img_path.exists():
        success = render_text_with_chrome(text, str(text_img_path), font_size=44)
        if not success:
            print(f"  [CHROME] Text render failed — using Pillow fallback")
            _render_with_pillow(text, str(text_img_path), font_size=44)

    return text_img_path if text_img_path.exists() else None


# ── Master audio assembler ─────────────────────────────────────────────────────
def build_master_audio(audio_clips: list) -> Optional[Path]:
    """
    Concatenate all per-sentence MP3s into ONE WAV, then loudnorm it.

    WHY ONE MASTER TRACK:
      Every per-clip AAC encode introduces ~2112 samples (44ms @ 48kHz) of
      encoder priming delay. Across 60+ clips this accumulates to >2 seconds
      of phantom audio — causing voice breaks and A/V drift that no per-clip
      fix can eliminate. One encode = zero accumulation.

    Strategy:
      1. Write a concat filter_complex that joins all MP3s back-to-back
         with the concat audio filter (not the demuxer — the filter resamples
         inline and produces a single seamless PCM stream).
      2. Apply loudnorm in the same pass — no inter-process handoff.
      3. Output: single 48kHz stereo WAV used by the final video encode.
    """
    master_raw  = OUTPUT_DIR / "master_audio_raw.wav"
    master_norm = OUTPUT_DIR / "master_audio_norm.wav"

    n = len(audio_clips)
    print(f"  [AUDIO] Assembling {n} clips into master track…")

    # Build filter_complex: [0:a][1:a]…[n-1:a] concat=n=N:v=0:a=1 [aout]
    # Each input is resampled to 48kHz/stereo inside the filter — no priming.
    inputs = []
    for p in audio_clips:
        inputs += ["-i", str(p)]

    filter_str = (
        "".join(f"[{i}:a]" for i in range(n))
        + f"concat=n={n}:v=0:a=1[aout]"
    )

    cmd_concat = [
        "ffmpeg", "-y",
        *inputs,
        "-filter_complex", filter_str,
        "-map", "[aout]",
        "-ar", "48000", "-ac", "2",
        str(master_raw),
    ]
    r = subprocess.run(cmd_concat, capture_output=True, text=True)
    if r.returncode != 0 or not master_raw.exists():
        print(f"  [AUDIO ERROR] concat failed:\n{r.stderr[-400:]}")
        return None

    print(f"  [AUDIO] Normalising master track (EBU R128)…")
    cmd_norm = [
        "ffmpeg", "-y",
        "-i", str(master_raw),
        "-af", "loudnorm=I=-16:TP=-1.5:LRA=11",
        "-ar", "48000", "-ac", "2",
        str(master_norm),
    ]
    rn = subprocess.run(cmd_norm, capture_output=True, text=True)
    if rn.returncode != 0 or not master_norm.exists():
        print(f"  [AUDIO WARN] loudnorm failed — using raw master")
        return master_raw

    master_raw.unlink(missing_ok=True)
    dur = get_duration(master_norm)
    print(f"  [AUDIO] Master track ready: {dur:.1f}s → {master_norm.name}")
    return master_norm


# ── Final video assembler ──────────────────────────────────────────────────────
def assemble_video(frame_paths: list, durations: list, master_audio: Path,
                   bg_image_paths: list = None) -> Path:
    """
    Encode each sentence into a silent video segment of exact duration,
    compositing background image + text overlay entirely inside FFmpeg.

    Background images are NEVER pre-processed by PIL — FFmpeg scale+pad is
    the single source of truth for output dimensions, so every segment is
    guaranteed to be exactly VIDEO_W x VIDEO_H regardless of source image
    size, aspect ratio, or whether multiple paragraphs share the same image.
    """
    import shutil
    segments_dir = OUTPUT_DIR / "segments"
    segments_dir.mkdir(exist_ok=True)

    if bg_image_paths is None:
        bg_image_paths = [""] * len(frame_paths)

    segment_paths = []
    print(f"  [ENCODE] Encoding {len(frame_paths)} video segments…")

    for i, (overlay_png, bg_path, dur) in enumerate(zip(frame_paths, bg_image_paths, durations)):
        # Segment cache key = hash of (bg path + overlay path) so any change
        # to either source invalidates the segment automatically.
        sig_src = f"{bg_path}|{overlay_png}"
        seg_sig = hashlib.md5(sig_src.encode()).hexdigest()[:8]
        seg = segments_dir / f"seg_{i:04d}_{seg_sig}.mp4"
        if seg.exists():
            segment_paths.append(seg)
            continue

        has_bg      = bg_path and Path(bg_path).exists()
        has_overlay = overlay_png and Path(overlay_png).exists()

        if has_bg and has_overlay:
            # Two inputs: background image + RGBA text overlay.
            # [0] bg scaled+padded to exact canvas size.
            # [1] overlay (RGBA) composited on top at (0,0).
            filter_complex = (
                f"[0:v]scale={VIDEO_W}:{VIDEO_H}:"
                f"force_original_aspect_ratio=decrease,"
                f"pad={VIDEO_W}:{VIDEO_H}:(ow-iw)/2:(oh-ih)/2:color=black,"
                f"setsar=1,format=yuv420p[bg];"
                f"[1:v]format=rgba[ov];"
                f"[bg][ov]overlay=0:0,setsar=1[out]"
            )
            cmd = [
                "ffmpeg", "-y",
                "-loop", "1", "-framerate", str(FPS), "-i", str(bg_path),
                "-loop", "1", "-framerate", str(FPS), "-i", str(overlay_png),
                "-t", f"{dur:.6f}",
                "-filter_complex", filter_complex,
                "-map", "[out]",
                "-c:v", "libx264", "-preset", "fast",
                "-pix_fmt", "yuv420p", "-r", str(FPS), "-an",
                str(seg),
            ]
        elif has_bg:
            # Background only — no overlay PNG
            cmd = [
                "ffmpeg", "-y",
                "-loop", "1", "-framerate", str(FPS), "-i", str(bg_path),
                "-t", f"{dur:.6f}",
                "-vf", (
                    f"scale={VIDEO_W}:{VIDEO_H}:force_original_aspect_ratio=decrease,"
                    f"pad={VIDEO_W}:{VIDEO_H}:(ow-iw)/2:(oh-ih)/2:color=black,setsar=1"
                ),
                "-c:v", "libx264", "-preset", "fast",
                "-pix_fmt", "yuv420p", "-r", str(FPS), "-an",
                str(seg),
            ]
        else:
            # No background — dark fallback + overlay if present
            bg_lavfi = f"color=c=0x0F1422:s={VIDEO_W}x{VIDEO_H}:r={FPS}"
            if has_overlay:
                filter_complex = (
                    f"[1:v]format=rgba[ov];"
                    f"[0:v][ov]overlay=0:0,setsar=1[out]"
                )
                cmd = [
                    "ffmpeg", "-y",
                    "-f", "lavfi", "-i", bg_lavfi,
                    "-loop", "1", "-framerate", str(FPS), "-i", str(overlay_png),
                    "-t", f"{dur:.6f}",
                    "-filter_complex", filter_complex,
                    "-map", "[out]",
                    "-c:v", "libx264", "-preset", "fast",
                    "-pix_fmt", "yuv420p", "-r", str(FPS), "-an",
                    str(seg),
                ]
            else:
                cmd = [
                    "ffmpeg", "-y",
                    "-f", "lavfi", "-i", bg_lavfi,
                    "-t", f"{dur:.6f}",
                    "-c:v", "libx264", "-preset", "fast",
                    "-pix_fmt", "yuv420p", "-r", str(FPS), "-an",
                    str(seg),
                ]

        r = subprocess.run(cmd, capture_output=True, text=True)
        if r.returncode != 0 or not seg.exists():
            print(f"  [SEG ERROR] segment {i}: {r.stderr[-300:]}")
            raise RuntimeError(f"Segment {i} encode failed")
        segment_paths.append(seg)

    # Write concat list for all video segments
    seg_list = OUTPUT_DIR / "segments_list.txt"
    with open(seg_list, "w", encoding="utf-8") as f:
        for sp in segment_paths:
            f.write(f"file '{sp.resolve()}'\n")

    # Silent concatenated video
    silent_video = OUTPUT_DIR / "silent_video.mp4"
    cmd_concat = [
        "ffmpeg", "-y",
        "-f", "concat", "-safe", "0", "-i", str(seg_list),
        "-c", "copy",
        str(silent_video),
    ]
    print(f"  [ENCODE] Concatenating {len(segment_paths)} segments…")
    r = subprocess.run(cmd_concat, capture_output=True, text=True)
    if r.returncode != 0 or not silent_video.exists():
        print(f"  [CONCAT ERROR]\n{r.stderr[-400:]}")
        raise RuntimeError("Segment concatenation failed")

    # Mux silent video + master audio → final output
    total_dur = sum(durations)
    cmd_mux = [
        "ffmpeg", "-y",
        "-i", str(silent_video),
        "-i", str(master_audio),
        "-c:v", "copy",
        "-c:a", "aac", "-b:a", "192k", "-ar", "48000", "-ac", "2",
        # Trim to exact total duration so neither stream overshoots
        "-t", f"{total_dur:.6f}",
        "-movflags", "+faststart",
        str(FINAL_VIDEO),
    ]
    print(f"  [ENCODE] Muxing audio + video (total {total_dur:.1f}s)…")
    r = subprocess.run(cmd_mux, capture_output=True, text=True)
    if r.returncode != 0:
        print(f"  [MUX ERROR]\n{r.stderr[-400:]}")
        raise RuntimeError("Final mux failed")

    # Cleanup intermediates
    seg_list.unlink(missing_ok=True)
    silent_video.unlink(missing_ok=True)
    shutil.rmtree(segments_dir, ignore_errors=True)

    return FINAL_VIDEO


# ── Main ───────────────────────────────────────────────────────────────────────
def main():
    print("=" * 70)
    print("  Hindi Video Generator V19 - Single-Pass Audio/Video")
    print(f"  Images : {IMAGE_BASE_DIR}")
    print("=" * 70)

    ensure_dirs()

    # ── Load image map from JSON or Excel (overrides hardcoded PARA_TO_IMAGE_MAP) ──
    global PARA_TO_IMAGE_MAP
    # Load image map exclusively from script_editor.xlsx (next to script, or via --image-map)
    auto_xlsx = SCRIPT_DIR / "script_editor.xlsx"

    if ARGS.image_map:
        map_path = ARGS.image_map
    elif auto_xlsx.exists():
        map_path = str(auto_xlsx)
    else:
        map_path = None

    if map_path:
        try:
            PARA_TO_IMAGE_MAP = load_image_map_from_excel(map_path)
            max_img_num = max(PARA_TO_IMAGE_MAP.values()) if PARA_TO_IMAGE_MAP else FALLBACK_IMAGE_NUM
            print(f"  [MAP] Loaded {len(PARA_TO_IMAGE_MAP)} paragraph→image entries from {map_path}")
            print(f"  [MAP] Image range: image0.jpeg … image{max_img_num}.jpeg")
        except Exception as e:
            print(f"  [MAP WARN] Could not load {map_path}: {e} — using fallback (all image0)")
    else:
        print("  [MAP] script_editor.xlsx not found — all paragraphs use image0 (fallback)")

    use_sarvam = not ARGS.no_sarvam
    if use_sarvam:
        print(f"  [TTS] Sarvam AI (shubh voice)")
    else:
        check_voice()
        print(f"  [TTS] macOS {TTS_VOICE}")

    # ── Decide image mode ──────────────────────────────────────────────────────
    # Single-image mode is active when any of these are true:
    #   a) --single-image flag passed on CLI
    #   b) --bg-image flag passed (explicit override path)
    #   c) USE_SINGLE_BG = True in config
    single_bg_override_path = None    # path string or None (None = multi-image mode)

    want_single = USE_SINGLE_BG or ARGS.single_image or bool(ARGS.bg_image)

    if want_single:
        # Resolve which single image to use
        chosen_path = ARGS.bg_image or DEFAULT_BG_IMAGE
        print(f"  [BG] Single-image mode → {chosen_path}")
        test = load_and_prepare_bg_image(chosen_path)
        if test:
            single_bg_override_path = chosen_path
            print(f"  [BG] Loaded: {test.size}")
        else:
            print("  [BG] Could not load image — using gradient fallback for all clips")
    else:
        # Multi-image mode: verify all mapped images exist upfront
        unique_imgs = sorted(set(PARA_TO_IMAGE_MAP.values()) | {FALLBACK_IMAGE_NUM})
        warnings = verify_images()
        if warnings:
            for w in warnings:
                print(w)
        print(f"  [BG] Multi-image mode — {len(unique_imgs)} unique images mapped ({', '.join(f'image{n}' for n in unique_imgs)})")

    # ── Parse script ──────────────────────────────────────────────────────────
    print("\n[1/4] Parsing article...")
    sections = parse_sections(str(ARTICLE_FILE))
    print(f"      {len(sections)} sections (paragraphs) found")

    total_sentences = sum(len(split_sentences(s["body"])) for s in sections)
    print(f"      {total_sentences} sentences total")

    # Show the paragraph → image mapping that will be used
    print("\n  Paragraph → Image mapping:")
    for i, sec in enumerate(sections):
        img_num   = _resolve_image_num(i)
        _rp       = resolve_image_file(img_num)
        img_file  = Path(_rp).name if _rp else f"image{img_num}.jpeg (missing)"
        title_preview = sec['title'][:35]
        print(f"    Para {i+1:2d} → image{img_num} ({img_file})  [{title_preview}]")

    # ── Phase 1: TTS — generate all audio clips (cached by text hash) ──────────
    print("\n[2/4] Generating audio + frames…")
    sentences_meta = []   # list of {text, img_path, audio_path, dur}
    idx = 0

    for sec_idx, section in enumerate(sections):
        sentences = split_sentences(section["body"])
        if ARGS.short:
            sentences = sentences[:MAX_SENTENCES_SHORT]

        if single_bg_override_path is not None:
            img_path = single_bg_override_path
        else:
            img_path = get_image_for_paragraph(sec_idx)

        img_num = _resolve_image_num(sec_idx)
        print(f"\n  ── Sec {sec_idx+1} [image{img_num}]: {section['title'][:40]} "
              f"[{len(sentences)} sent]  bg={Path(img_path).name}")

        for sent in sentences:
            if len(sent) < 4:
                continue
            audio_path, dur = generate_audio(sent, idx, use_sarvam)
            print(f"    [{idx:3d}] {dur:4.1f}s | {sent[:55]}…")
            sentences_meta.append({
                "text":       sent,
                "img_path":   img_path,
                "audio_path": audio_path,
                "dur":        dur,
                "idx":        idx,
            })
            idx += 1

    # ── Phase 2: Compose frames (PNG only, no audio encode per frame) ──────────
    print(f"\n  Composing {len(sentences_meta)} frames…")

    # Keep overlays, bg paths, audio/duration in lockstep.
    # compose_frame now returns only the text overlay PNG (transparent bg).
    # The background image is passed separately to assemble_video so FFmpeg
    # composites both at encode time — single source of truth for dimensions.
    overlay_paths    = []
    bg_paths         = []
    durations        = []
    audio_for_master = []

    for m in sentences_meta:
        fp = compose_frame(m["img_path"], m["text"], m["idx"])
        if fp:
            overlay_paths.append(fp)
            bg_paths.append(m["img_path"])
            durations.append(m["dur"])
            audio_for_master.append(m["audio_path"])
        else:
            print(f"    [WARN] Overlay {m['idx']} failed — dropping sentence from video")

    if not overlay_paths:
        raise RuntimeError("No overlays were generated — aborting")

    # ── Phase 3: Build ONE master audio track (no per-clip AAC encoding) ───────
    print(f"\n[3/4] Building master audio track…")
    master_audio = build_master_audio(audio_for_master)
    if master_audio is None:
        raise RuntimeError("Master audio assembly failed — aborting")

    # ── Phase 4: Single-pass video encode ─────────────────────────────────────
    total_dur = sum(durations)
    final = assemble_video(overlay_paths, durations, master_audio, bg_image_paths=bg_paths)

    # Clean up overlay PNGs (encoded into video)
    for fp in TEXT_IMG_DIR.glob("text_*.png"):
        pass  # keep text_images cache for reruns — only wipe on --clean-clips

    mins, secs = divmod(int(total_dur), 60)
    size_mb    = os.path.getsize(final) / (1024 * 1024) if final.exists() else 0

    print("\n" + "=" * 70)
    print(f"  ✅ Video ready!")
    print(f"      File      : {final}")
    print(f"      Size      : {size_mb:.1f} MB")
    print(f"      Sentences : {len(overlay_paths)}")
    print(f"      Duration  : ~{mins}m {secs}s")
    print(f"      Resolution: {VIDEO_W}x{VIDEO_H}")
    print(f"      Frame rate: {FPS}fps")
    print("=" * 70)

    return final


if __name__ == "__main__":
    main()
