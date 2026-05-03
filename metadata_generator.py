#!/usr/bin/env python3
"""
metadata_generator.py
Generates YouTube title, description, and tags from a script file using OpenAI.
Usage: python3 metadata_generator.py <script_path> <openai_api_key>
"""
import sys
import json
import urllib.request
import traceback


def extract(text, start_marker, end_marker):
    try:
        start = text.index(start_marker) + len(start_marker)
        end = text.index(end_marker, start)
        return text[start:end].strip()
    except ValueError:
        return ""


def main():
    script_path = sys.argv[1]
    api_key = sys.argv[2]

    with open(script_path, encoding="utf-8") as f:
        script = f.read()

    system_msg = (
        "You are a YouTube SEO expert specialising in Hindi/Hinglish "
        "cyber fraud awareness content for Indian audiences."
    )

    user_prompt = "\n".join([
        "You are a YouTube SEO expert for Banking Expert Ram (@bankingexpertram),",
        "a Hinglish channel run by a retired SBI banking expert, focused on cyber",
        "fraud awareness, banking safety, and financial scam alerts for common Indians.",
        "",
        "Generate YouTube metadata for the video script below.",
        "Use EXACTLY this format with these exact markers:",
        "",
        "##TITLE##",
        "SEO-optimized title (max 70 chars, urgent tone, Hindi Devanagari/Hinglish mix)",
        "##END_TITLE##",
        "",
        "##DESCRIPTION##",
        "200-250 word engaging description in Hinglish (Hindi Devanagari 70%, English 30%).",
        "- Start with a strong warning or shocking statistic about the fraud",
        "- Mention Banking Expert Ram and @bankingexpertram channel",
        "- Explain what viewers will learn",
        "- Mention Ram's 39 years of SBI banking experience",
        "- End with: Subscribe kare @bankingexpertram ko aur apne parivaar ko safe rakhe!",
        "- Add 8-10 relevant hashtags at the very end",
        "##END_DESCRIPTION##",
        "",
        "##TAGS##",
        "15-20 tags comma-separated, English+Hindi mix, must include: cyber fraud,",
        "banking fraud, cyber crime India, Banking Expert Ram, bankingexpertram,",
        "SBI fraud alert, online fraud India, digital fraud India, financial scam alert",
        "##END_TAGS##",
        "",
        "Script:",
        script,
    ])

    payload = json.dumps({
        "model": "gpt-4.1-mini",
        "max_tokens": 2000,
        "temperature": 0.7,
        "messages": [
            {"role": "system", "content": system_msg},
            {"role": "user", "content": user_prompt},
        ],
    }).encode("utf-8")

    try:
        req = urllib.request.Request(
            "https://api.openai.com/v1/chat/completions",
            data=payload,
            headers={
                "Content-Type": "application/json",
                "Authorization": f"Bearer {api_key}",
            },
            method="POST",
        )
        with urllib.request.urlopen(req, timeout=60) as resp:
            body = json.loads(resp.read().decode("utf-8"))

        if "error" in body:
            raise ValueError(f"OpenAI error: {json.dumps(body['error'])}")

        raw = body["choices"][0]["message"]["content"]

        title = extract(raw, "##TITLE##", "##END_TITLE##")
        description = extract(raw, "##DESCRIPTION##", "##END_DESCRIPTION##")
        tags_raw = extract(raw, "##TAGS##", "##END_TAGS##")
        tags = [t.strip() for t in tags_raw.split(",") if t.strip()]

        if not title:
            raise ValueError(f"Could not extract TITLE from response:\n{raw[:500]}")

        print(json.dumps(
            {"success": True, "title": title, "description": description, "tags": tags},
            ensure_ascii=False,
        ))

    except Exception as e:
        print(json.dumps(
            {"success": False, "error": str(e), "trace": traceback.format_exc()[-500:]},
            ensure_ascii=False,
        ))


if __name__ == "__main__":
    main()
