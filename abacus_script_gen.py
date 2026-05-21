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
    "You are a world-class Hinglish content writer for @bankingexpertram YouTube — "
    "covering cybersecurity, banking rights, govt schemes, digital tools, and consumer rights "
    "for common Indians. Channel: Ram Krishan Dudeja, retired SBI AGM, CISA certified, 39 years banking experience.\n\n"
    "CRITICAL SCRIPT RULE — DEVANAGARI SCRIPT MANDATORY:\n"
    "All Hindi words MUST be written in Devanagari script (देवनागरी). "
    "NEVER write Hindi words in Roman/English letters. "
    "Only keep in Roman script: English technical terms (UPI, OTP, ATM, SIM, KYC, CIBIL), "
    "brand names (WhatsApp, Google, IRCTC), portal URLs, and numbers. "
    "WRONG: 'Aapke paas rights hain' — RIGHT: 'आपके पास rights हैं' "
    "WRONG: 'Yeh scam se bachne ke liye' — RIGHT: 'यह scam से बचने के लिए'"
)

# Category-specific content flow rules
_CONTENT_FLOW = {
    "Cybersecurity": (
        "First paragraph: shocking fraud statistic or recent national incident as hook\n"
        "Middle paragraphs: relatable victim scenario + how the scam works step-by-step + red flags + prevention tips\n"
        "Last paragraph: urgent emotional CTA — share this video. End with: helpline 1930, cybercrime.gov.in, @bankingexpertram channel ko subscribe करें"
    ),
    "Banking rights": (
        "First paragraph: shocking RBI stat or relatable bank injustice hook\n"
        "Middle paragraphs: your legal RBI rights + step-by-step complaint process + key deadlines + real example\n"
        "Last paragraph: empowering CTA — aap ke paas rights hain, use them. End with: helpline 1930, cybercrime.gov.in, @bankingexpertram channel ko subscribe करें"
    ),
    "Govt schemes": (
        "First paragraph: common painful problem this scheme solves, or money/time wasted without knowing it\n"
        "Middle paragraphs: official portal steps + documents needed + common mistakes + fake-site/scam warning\n"
        "Last paragraph: CTA — sirf official portal use karein. End with: helpline 1930, cybercrime.gov.in, @bankingexpertram channel ko subscribe करें"
    ),
    "Digital tools": (
        "First paragraph: shocking stat about how many people miss this tool, or relatable inconvenience it solves\n"
        "Middle paragraphs: step-by-step setup + key features + real benefit + one common mistake to avoid\n"
        "Last paragraph: encouraging CTA — aaj hi try karein. End with: helpline 1930, cybercrime.gov.in, @bankingexpertram channel ko subscribe करें"
    ),
    "Consumer rights": (
        "First paragraph: relatable consumer injustice — money lost, ignored complaint, unfair company\n"
        "Middle paragraphs: your legal rights + escalation steps (company → regulator/ombudsman → consumer forum) + portal + cost/timeline\n"
        "Last paragraph: empowering CTA — aapko haarna nahi chahiye. End with: helpline 1930, cybercrime.gov.in, @bankingexpertram channel ko subscribe करें"
    ),
}


def _get_content_flow(topic: str) -> str:
    import re
    m = re.search(r'\[Category:\s*([^\]]+)\]', topic)
    cat = m.group(1).strip() if m else "Cybersecurity"
    return _CONTENT_FLOW.get(cat, _CONTENT_FLOW["Cybersecurity"])


def build_user_prompt(topic: str) -> str:
    content_flow = _get_content_flow(topic)
    return "\n".join([
        f"Create a highly engaging Hinglish script for a YouTube video on:",
        f"{topic}",
        "",
        "STRICT STRUCTURE RULES:",
        "1. Exactly ONE title/heading at the very top (single line, starting with #)",
        "2. Between 5 and 7 paragraphs of body text — NO headings, NO captions, NO labels between paragraphs",
        "3. Total word count: 350-500 words (3-4 minutes speaking time)",
        "4. Each paragraph: 50-75 words, flows naturally into the next",
        "",
        "CONTENT FLOW FOR THIS CATEGORY:",
        content_flow,
        "",
        "SCRIPT & LANGUAGE RULES — STRICTLY ENFORCED:",
        "1. ALL Hindi words MUST be in Devanagari script — NEVER in Roman/English letters",
        "2. Target: 70-80% Devanagari text, 20-30% English (only technical terms, brand names, numbers)",
        "3. The # title line: also write Hindi words in Devanagari",
        "4. Example of correct style: 'आज हम बात करेंगे एक ऐसे scam के बारे में जो आपके account को खाली कर सकता है।'",
        "5. Example of WRONG style (DO NOT do this): 'Aaj hum baat karenge ek aise scam ke baare mein'",
        "6. Plain paragraphs only — no bullet points, no numbered lists, no markdown except the single # title",
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
