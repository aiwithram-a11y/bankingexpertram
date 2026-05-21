# BankingExpertRam YouTube Pipeline

## Purpose
Hindi cybersecurity awareness YouTube automation for @bankingexpertram channel.
Owner: Ram Krishan Dudeja, RamKrishan Advisory, Faridabad

## Pipeline Flow
**Daily entry point:** `python3 daily_script.py` (prompts for ddmmyyyy date → generates script.md)
script_to_excel.py → excel_to_video.py → video_generator.py
Output lands in output_v19/

## n8n Workflow
- Reads video + metadata from this folder
- Uploads to YouTube via Google API
- n8n runs at localhost:5678
- **n8n Environment Variables UI is enterprise-only** — not available on self-hosted free tier
- Project path is hardcoded in workflow JSON nodes AND set in `/Users/ramdudeja/.n8n/.env` as `BANKING_EXPERT_DIR`
- n8n file access configured in `/Users/ramdudeja/.n8n/.env` (system config, not project secrets)

## AI Stack (as of May 2026)
- **Abacus.AI** — primary AI provider (API key in .abacus_key)
  - Script generation: abacus_script_gen.py (Claude Sonnet 4.6 via Abacus)
  - Image prompt generation: Abacus.AI node in n8n (Claude Sonnet 4.6)
  - YouTube metadata: metadata_generator.py (Claude Sonnet 4.6 via Abacus)
  - Image generation: abacus_image_gen.py (GPT Image 1.5 via Abacus)
- **Sarvam AI** — Hindi TTS (bulbul:v3, "shubh" voice) — unchanged
- **FFmpeg** — video composition — unchanged

## Key Rules
- Never modify project .env files (API keys/secrets)
- `/Users/ramdudeja/.n8n/.env` is n8n system config — CAN be modified for path/access settings
- Don't read binary/video files
- .abacus_key holds the Abacus.AI API key (format: s2_...)
- Python scripts use Sarvam AI TTS (bulbul:v3, "shubh" voice)
- FFmpeg used for all video composition
- abacusai Python package required: pip install abacusai

## Abacus.AI Integration Files
- daily_script.py — **new daily entry point**: date lookup → script.md generation
- abacus_script_gen.py — script generation (category-aware prompts for all 5 topic types)
- abacus_image_gen.py — image generation (GPT Image 1.5)
- abacus_image_prompt_gen.py — image prompts (visual tone adapts to topic category)
- metadata_generator.py — YouTube metadata

## Content Categories (bankingexpertram_content_calendar.md)
- Cybersecurity | Banking rights | Govt schemes | Digital tools | Consumer rights
- Calendar: 30 topics, 19 May – 17 Jun 2026
- CTA on every video: helpline 1930 | cybercrime.gov.in | RamKrishan Advisory

## Ignore
node_modules/, output_v19/audio/, output_v19/text_images/
