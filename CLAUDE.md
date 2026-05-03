# BankingExpertRam YouTube Pipeline

## Purpose
Hindi cybersecurity awareness YouTube automation for @bankingexpertram channel.
Owner: Ram Krishan Dudeja, RamKrishan Advisory, Faridabad

## Pipeline Flow
script_to_excel.py → excel_to_video.py → generate_video_different_images.py
Output lands in output_v19/

## n8n Workflow
- Reads video + metadata from this folder
- Uploads to YouTube via Google API
- n8n runs at localhost:5678

## Key Rules
- Never modify .env files
- Don't read binary/video files
- Python scripts use Sarvam AI TTS (bulbul:v3, "shubh" voice)
- FFmpeg used for all video composition

## Ignore
node_modules/, output_v19/audio/, output_v19/text_images/
