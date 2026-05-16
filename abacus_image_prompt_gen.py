#!/usr/bin/env python3
"""
abacus_image_prompt_gen.py
Generates DALL-E / image generation prompts for each paragraph using Abacus.AI.
Called by the n8n '🎨 Abacus.AI: Generate Image Prompts' node.

Usage:
    python3 abacus_image_prompt_gen.py <abacus_key> <images_needed> <input_file> <output_file>

    input_file  — text file with numbered paragraphs (written by n8n)
    output_file — JSON output path (optional, also printed to stdout)

Output (stdout): JSON {"success": true, "prompts": ["prompt1", "prompt2", ...]}
"""
import sys
import json
import traceback


SYSTEM_MSG = (
    "You generate image prompts for a Hindi YouTube cybersecurity awareness channel (@bankingexpertram). "
    "All characters must look visually Hindu Indian. "
    "Women wear sari or salwar kameez with bindi on forehead — NEVER hijab or Islamic dress. "
    "Men wear kurta-pyjama or casual Indian clothes — NO skull cap. "
    "Elderly: white kurta-dhoti. Middle-class Indian appearance throughout. "
    "Images must be ultra-realistic photographic quality with ABSOLUTELY NO text, "
    "NO speech bubbles, NO captions, NO writing of any kind anywhere in the image."
)


def build_user_prompt(images_needed: int, numbered_paragraphs: str) -> str:
    return f"""Generate exactly {images_needed} image prompts, one per numbered paragraph below.

For each paragraph, create a prompt for a 2-panel photorealistic diptych (two side-by-side scenes separated by a thin black border, widescreen 16:9) that visually tells the key emotional moment of that paragraph.

IMPORTANT — LAST IMAGE RULE: The very last prompt (paragraph {images_needed}) must show a HAPPY, SECURE, RELIEVED tone — a warm concluding scene. Show a smiling Indian family or individual feeling safe, confident, and protected after learning about cyber safety. Warm golden lighting, positive body language, sense of relief and empowerment. NOT dramatic, NOT fearful — uplifting and hopeful.

STRICT CHARACTER RULES — every character must look visually Hindu Indian:
- Women: sari or salwar kameez, bindi on forehead, bangles
- Men: kurta-pyjama or casual Indian clothes, optional tilak
- Elderly: white kurta-dhoti or kurta-pyjama
- Middle-class Indian appearance throughout

STRICT NO-TEXT RULES — most important rule:
- ZERO text anywhere — no speech bubbles, no captions, no labels, no Hindi, no English
- Pure visual storytelling through expressions, gestures, body language, environment

STYLE: Ultra-realistic cinematic photography — dramatic lighting, shallow depth of field, warm Indian home/street/office environments, highly expressive faces, professional photo-journalism level realism.

Return ONLY a valid JSON array of strings (one prompt per element). No explanation, no markdown, just the JSON array.

Paragraphs:
{numbered_paragraphs}"""


def main():
    if len(sys.argv) < 5:
        print(json.dumps({"success": False, "error": "Usage: abacus_image_prompt_gen.py <api_key> <images_needed> <input_file> <output_file>"}))
        sys.exit(1)

    api_key       = sys.argv[1]
    images_needed = int(sys.argv[2])
    input_file    = sys.argv[3]
    output_file   = sys.argv[4]

    with open(input_file, encoding="utf-8") as f:
        numbered_paragraphs = f.read().strip()

    try:
        from abacusai import ApiClient
        client = ApiClient(api_key)

        resp = client.evaluate_prompt(
            system_message=SYSTEM_MSG,
            prompt=build_user_prompt(images_needed, numbered_paragraphs),
            llm_name="CLAUDE_V4_6_SONNET",
            max_tokens=3000,
            temperature=0.7,
        )

        content = resp.content.strip()

        # Extract JSON array from response
        import re
        m = re.search(r'\[[\s\S]*\]', content)
        if m:
            prompts = json.loads(m.group(0))
        else:
            # Fallback: parse numbered lines
            lines = [l.strip() for l in content.split('\n') if l.strip()]
            prompts = []
            for line in lines:
                line = re.sub(r'^\d+[\.\)]\s*', '', line).strip().strip('"')
                if len(line) > 20:
                    prompts.append(line)

        if not prompts:
            raise ValueError(f"Could not extract prompts from response: {content[:300]}")

        result = {"success": True, "prompts": prompts, "count": len(prompts)}
        output = json.dumps(result, ensure_ascii=False)

        # Write to output file
        with open(output_file, "w", encoding="utf-8") as f:
            f.write(output)

        print(output)

    except Exception as e:
        print(json.dumps({
            "success": False,
            "error": str(e),
            "trace": traceback.format_exc()[-500:],
        }, ensure_ascii=False))


if __name__ == "__main__":
    main()
