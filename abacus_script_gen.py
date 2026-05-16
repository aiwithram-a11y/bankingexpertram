#!/usr/bin/env python3
"""
abacus_script_gen.py
Generates a Hindi/Hinglish cybersecurity awareness script using Abacus.AI.
Called from n8n to replace the Anthropic Claude API node.

Usage:
    python3 abacus_script_gen.py <topic> <abacus_api_key>

Output: JSON  {"success": true, "script": "...", "model": "..."}
              {"success": false, "error": "..."}
"""
import sys
import json
import traceback


SYSTEM_PROMPT = (
    "You are a world-class Hindi content writer and expert storyteller for YouTube "
    "educational videos, especially on cybercrime awareness for common Indians."
)

def build_user_prompt(topic: str) -> str:
    return "\n".join([
        f"Create a highly engaging Hindi script for a YouTube video on: {topic}",
        "",
        "STRICT STRUCTURE RULES:",
        "1. Exactly ONE title/heading at the very top (single line, starting with #)",
        "2. Exactly 4 to 6 paragraphs of body text below the title — NO headings, NO captions, NO labels between paragraphs",
        "3. Total word count: 300-375 words (2-3 minutes speaking time at natural pace)",
        "4. Each paragraph: 50-75 words, flows naturally into the next",
        "",
        "CONTENT RULES:",
        "1. Written in simple conversational Hinglish (Hindi Devanagari 70-80%, English mix)",
        "2. First paragraph: powerful hook or shocking real statistic",
        "3. Middle paragraphs: real-life relatable scenario + how the scam works + warning signs + prevention",
        "4. Last paragraph: strong emotional call to action mentioning @bankingexpertram",
        "6. Plain paragraphs only — absolutely no bullet points, no numbered lists, no markdown formatting except the single # title",
        "",
        "Channel context: Banking Expert Ram (@bankingexpertram) — cyber fraud awareness for common Indians.",
    ])


def main():
    if len(sys.argv) < 3:
        print(json.dumps({"success": False, "error": "Usage: abacus_script_gen.py <topic> <api_key>"}))
        sys.exit(1)

    topic = sys.argv[1]
    api_key = sys.argv[2]

    try:
        from abacusai import ApiClient
        client = ApiClient(api_key)

        resp = client.evaluate_prompt(
            system_message=SYSTEM_PROMPT,
            prompt=build_user_prompt(topic),
            llm_name="CLAUDE_V4_6_SONNET",
            max_tokens=4096,
            temperature=0.7,
        )

        script_text = resp.content.strip()
        if not script_text:
            raise ValueError("Empty script returned from model")

        print(json.dumps({
            "success": True,
            "script": script_text,
            "model": resp.llm_name,
            "tokens": resp.total_tokens,
        }, ensure_ascii=False))

    except Exception as e:
        print(json.dumps({
            "success": False,
            "error": str(e),
            "trace": traceback.format_exc()[-500:],
        }, ensure_ascii=False))


if __name__ == "__main__":
    main()
