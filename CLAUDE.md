# BankingExpertRam YouTube Pipeline

## Purpose
Hindi cybersecurity awareness YouTube automation for @bankingexpertram channel.
Owner: Ram Krishan Dudeja, RamKrishan Advisory, Faridabad

## Pipeline Flow
script_to_excel.py → excel_to_video.py → video_generator.py
Output lands in output_v19/

## n8n Workflow
- Reads video + metadata from this folder
- Uploads to YouTube via Google API
- n8n runs at localhost:5678

## AI Stack (as of May 2026)
- **Abacus.AI** — primary AI provider (API key in .abacus_key)
  - Script generation: abacus_script_gen.py (Claude Sonnet 4.6 via Abacus)
  - Image prompt generation: Abacus.AI node in n8n (Claude Sonnet 4.6)
  - YouTube metadata: metadata_generator.py (Claude Sonnet 4.6 via Abacus)
  - Image generation: abacus_image_gen.py (GPT Image 1.5 via Abacus)
- **Sarvam AI** — Hindi TTS (bulbul:v3, "shubh" voice) — unchanged
- **FFmpeg** — video composition — unchanged

## Key Rules
- Never modify .env files
- Don't read binary/video files
- .abacus_key holds the Abacus.AI API key (format: s2_...)
- Python scripts use Sarvam AI TTS (bulbul:v3, "shubh" voice)
- FFmpeg used for all video composition
- abacusai Python package required: pip install abacusai

## Abacus.AI Integration Files
- abacus_script_gen.py — Hindi script generation (replaces Anthropic API)
- abacus_image_gen.py — image generation (replaces DALL-E direct calls)
- metadata_generator.py — YouTube metadata (uses Abacus.AI SDK)

## Ignore
node_modules/, output_v19/audio/, output_v19/text_images/
