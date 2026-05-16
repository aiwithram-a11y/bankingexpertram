#!/usr/bin/env python3
"""
abacus_image_gen.py
Generates images using Abacus.AI Route LLM API and saves to disk.
Called from n8n to replace the OpenAI DALL-E image generation node.

Usage:
    python3 abacus_image_gen.py <prompt_file> <output_path> <abacus_api_key> [model]

    prompt_file — path to a text file containing the image prompt (avoids shell escaping)
    model: flux_pro (default) | gpt_image15 | flux2_pro | dalle | ideogram | recraft

Output: JSON  {"success": true, "path": "...", "model": "...", "size_kb": 123}
              {"success": false, "error": "..."}
"""
import sys
import json
import os
import traceback
import base64


ROUTE_LLM_ENDPOINT = 'https://apps.abacus.ai/v1/chat/completions'

DEFAULT_MODEL = 'flux_pro'

SUPPORTED_MODELS = {
    'flux_pro', 'flux2_pro', 'flux_pro_ultra', 'gpt_image15', 'gpt_image2',
    'dalle', 'imagen', 'ideogram', 'recraft', 'seedream', 'midjourney',
    'hunyuan_image', 'flux2',
}


def generate_image(prompt: str, output_path: str, api_key: str, model: str) -> dict:
    import requests

    if model not in SUPPORTED_MODELS:
        model = DEFAULT_MODEL

    headers = {
        'Content-Type': 'application/json',
        'Authorization': f'Bearer {api_key}',
        # Browser-like User-Agent required to reach apps.abacus.ai
        'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36',
    }

    payload = {
        'model': model,
        'messages': [{'role': 'user', 'content': prompt}],
        'modalities': ['image'],
    }

    resp = requests.post(ROUTE_LLM_ENDPOINT, json=payload, headers=headers, timeout=300)
    resp.raise_for_status()

    data = resp.json()
    choices = data.get('choices', [])
    if not choices:
        raise ValueError(f'No choices in response: {json.dumps(data)[:300]}')

    message = choices[0].get('message', {})

    # Image data is in message.images (not message.content)
    images = message.get('images', [])
    if not images:
        # Fallback: check content field for data URI
        content = message.get('content', '')
        if isinstance(content, str) and content.startswith('data:image'):
            images = [{'type': 'image_url', 'image_url': {'url': content}}]
        elif isinstance(content, list):
            images = [item for item in content if item.get('type') == 'image_url']

    if not images:
        raise ValueError(f'No image data in response. Message keys: {list(message.keys())}')

    image_url = images[0].get('image_url', {}).get('url', '')
    if not image_url:
        raise ValueError(f'No image URL found in: {json.dumps(images[0])[:300]}')

    # Decode base64 image data
    if ',' in image_url:
        header, b64_data = image_url.split(',', 1)
    else:
        b64_data = image_url

    img_bytes = base64.b64decode(b64_data)

    os.makedirs(os.path.dirname(os.path.abspath(output_path)), exist_ok=True)

    # Save and convert to JPEG
    tmp_path = output_path + '.tmp.png'
    with open(tmp_path, 'wb') as f:
        f.write(img_bytes)

    try:
        from PIL import Image
        img = Image.open(tmp_path)
        if img.mode in ('RGBA', 'P', 'LA'):
            img = img.convert('RGB')
        # Resize if too large (keep 16:9 friendly)
        max_w = 1792
        if img.width > max_w:
            ratio = max_w / img.width
            img = img.resize((max_w, int(img.height * ratio)), Image.LANCZOS)
        img.save(output_path, 'JPEG', quality=92, optimize=True)
        os.remove(tmp_path)
    except Exception:
        # If Pillow fails, save as-is and rename
        if os.path.exists(tmp_path):
            os.rename(tmp_path, output_path)

    return {'success': True, 'path': output_path, 'model': model}


def main():
    if len(sys.argv) < 4:
        print(json.dumps({
            'success': False,
            'error': 'Usage: abacus_image_gen.py <prompt_file> <output_path> <api_key> [model]',
        }))
        sys.exit(1)

    prompt_file = sys.argv[1]
    output_path = sys.argv[2]
    api_key     = sys.argv[3]
    model       = sys.argv[4] if len(sys.argv) > 4 else DEFAULT_MODEL

    with open(prompt_file, encoding='utf-8') as f:
        prompt = f.read().strip()

    try:
        result = generate_image(prompt, output_path, api_key, model)
        size_kb = os.path.getsize(output_path) // 1024 if os.path.exists(output_path) else 0
        result['size_kb'] = size_kb
        print(json.dumps(result, ensure_ascii=False))

    except Exception as e:
        print(json.dumps({
            'success': False,
            'error': str(e),
            'trace': traceback.format_exc()[-800:],
        }, ensure_ascii=False))


if __name__ == '__main__':
    main()
