# Banking Expert Ram — YouTube Automation Pipeline

Automated Hindi/Hinglish YouTube video pipeline for **@bankingexpertram** — a cyber fraud awareness channel run by Ram Krishan Dudeja, a retired SBI banking expert with 39 years of experience.

## What It Does

Takes a topic → generates a complete YouTube-ready video with Hindi voiceover, AI images, and SEO metadata — fully automated via n8n.

## Pipeline Flow

```
Topic (n8n Form)
    ↓
WF1: Claude API generates Hinglish script
    ↓
WF2: DALL-E 3 generates images → script_to_excel.py creates Excel control panel
    ↓
WF3: excel_to_video.py + video_generator.py → FFmpeg assembles final_video.mp4
     metadata_generator.py → YouTube title, description, tags (GPT-4.1-mini)
    ↓
WF4: n8n uploads video to YouTube + sets thumbnail (image0.jpeg)
```

## Tech Stack

| Component | Tool |
|-----------|------|
| Orchestration | n8n (self-hosted) |
| Script writing | Claude claude-opus-4-6 (Anthropic) |
| Image generation | DALL-E 3 (OpenAI) |
| Hindi TTS | Sarvam AI `bulbul:v3` — `shubh` voice |
| YouTube metadata | GPT-4.1-mini (OpenAI) |
| Video assembly | FFmpeg + Pillow/Playwright |
| Upload | YouTube Data API v3 via n8n |

## Files

| File | Purpose |
|------|---------|
| `bankingexpertram_workflow.json` | n8n workflow — import this into n8n |
| `script_to_excel.py` | Converts script to Excel control panel for image mapping |
| `excel_to_video.py` | Reads edited Excel → generates revised script + image map |
| `video_generator.py` | Assembles final video with TTS audio and images |
| `metadata_generator.py` | Calls GPT-4.1-mini to generate YouTube title/description/tags |

## Setup

### 1. Prerequisites

```bash
pip install openpyxl pandas pillow playwright
playwright install chromium
brew install ffmpeg
```

### 2. API Keys

Create `.openai_key` in the project folder:
```
sk-your-openai-key-here
```

### 3. n8n

- Self-hosted n8n at `localhost:5678`
- Import `bankingexpertram_workflow.json`
- Set environment variable in n8n:  
  `BANKING_EXPERT_DIR=/Users/yourname/Desktop/bankingexpertram`
- Add credentials: Anthropic API, OpenAI API, Sarvam AI, YouTube OAuth2

### 4. Images folder

Place 10 DALL-E generated images named `image0.jpeg` through `image9.jpeg` in the `images/` folder.  
`image0.jpeg` is always used as the YouTube thumbnail.

## Output

All generated files land in `output_v19/`:
- `final_video.mp4` — upload-ready video
- `audio/` — per-paragraph Hindi TTS audio
- `text_images/` — rendered text overlay frames

## Channel

[@bankingexpertram](https://www.youtube.com/@bankingexpertram) — Cyber fraud awareness for common Indians.
