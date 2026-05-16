#!/usr/bin/env python3
"""
youtube_upload.py
Uploads a video to YouTube using saved OAuth token (installed-app flow).
First run opens browser for one-time login. Subsequent runs are fully automatic.

Usage:
    python3 youtube_upload.py                         # reads pipeline_meta.json
    python3 youtube_upload.py --meta pipeline_meta.json
    python3 youtube_upload.py --video final.mp4 --title "Title" --desc "Desc"

Output: JSON {"success": true, "video_id": "...", "url": "..."}
"""
import sys
import os
import json
import argparse
import traceback
from pathlib import Path

SCRIPT_DIR       = Path(__file__).parent
CLIENT_SECRETS   = SCRIPT_DIR / 'client_secrets.json'
TOKEN_FILE       = SCRIPT_DIR / 'youtube_token.json'
PIPELINE_META    = SCRIPT_DIR / 'pipeline_meta.json'
OUTPUT_DIR       = SCRIPT_DIR / 'output_v19'

SCOPES = [
    'https://www.googleapis.com/auth/youtube.upload',
    'https://www.googleapis.com/auth/youtube.force-ssl',  # needed to delete auto-captions
]

CATEGORY_EDUCATION = '27'   # Education


def get_credentials():
    """Load saved token or do one-time OAuth browser flow."""
    from google.oauth2.credentials import Credentials
    from google.auth.transport.requests import Request
    from google_auth_oauthlib.flow import InstalledAppFlow

    creds = None

    # Load saved token if it exists
    if TOKEN_FILE.exists():
        creds = Credentials.from_authorized_user_file(str(TOKEN_FILE), SCOPES)

    # Refresh if expired
    if creds and creds.expired and creds.refresh_token:
        try:
            creds.refresh(Request())
            TOKEN_FILE.write_text(creds.to_json())
            return creds
        except Exception:
            creds = None   # force re-login

    # One-time browser login
    if not creds or not creds.valid:
        if not CLIENT_SECRETS.exists():
            raise FileNotFoundError(f'client_secrets.json not found at {CLIENT_SECRETS}')
        flow = InstalledAppFlow.from_client_secrets_file(str(CLIENT_SECRETS), SCOPES)
        creds = flow.run_local_server(port=0, open_browser=True)
        TOKEN_FILE.write_text(creds.to_json())

    return creds


def find_video(video_path=None):
    """Find the video file to upload."""
    if video_path and Path(video_path).exists():
        return Path(video_path)
    # Auto-discover latest mp4 in output_v19/
    candidates = sorted(OUTPUT_DIR.glob('*.mp4'), key=lambda p: p.stat().st_mtime, reverse=True)
    if candidates:
        return candidates[0]
    raise FileNotFoundError(f'No .mp4 found in {OUTPUT_DIR}')


def find_thumbnail(video_path: Path):
    """Find thumbnail image (image0.jpeg in images/ folder)."""
    thumb = SCRIPT_DIR / 'images' / 'image0.jpeg'
    if thumb.exists():
        return thumb
    thumb_png = SCRIPT_DIR / 'images' / 'image0.png'
    if thumb_png.exists():
        return thumb_png
    return None


def upload_video(creds, video_path: Path, title: str, description: str,
                 tags: list, category: str = CATEGORY_EDUCATION,
                 privacy: str = 'public') -> dict:
    from googleapiclient.discovery import build
    from googleapiclient.http import MediaFileUpload

    youtube = build('youtube', 'v3', credentials=creds)

    body = {
        'snippet': {
            'title':       title[:100],
            'description': description[:5000],
            'tags':        tags[:500],
            'categoryId':  category,
            'defaultLanguage': 'hi',
        },
        'status': {
            'privacyStatus':          privacy,
            'selfDeclaredMadeForKids': False,
        },
    }

    media = MediaFileUpload(
        str(video_path),
        mimetype='video/mp4',
        resumable=True,
        chunksize=1024 * 1024 * 8,   # 8 MB chunks
    )

    print(f'  Uploading: {video_path.name} ({video_path.stat().st_size // 1024 // 1024} MB)...')

    request  = youtube.videos().insert(part='snippet,status', body=body, media_body=media)
    response = None
    while response is None:
        status, response = request.next_chunk()
        if status:
            pct = int(status.progress() * 100)
            print(f'  Progress: {pct}%', end='\r')

    video_id = response['id']
    print(f'\n  Uploaded: https://www.youtube.com/watch?v={video_id}')
    return {'video_id': video_id, 'url': f'https://www.youtube.com/watch?v={video_id}'}


def disable_auto_captions(creds, video_id: str, retries: int = 5, wait: int = 20):
    """Delete YouTube auto-generated (ASR) captions. Retries because YT takes time to generate them."""
    import time
    from googleapiclient.discovery import build

    youtube = build('youtube', 'v3', credentials=creds)
    for attempt in range(retries):
        resp  = youtube.captions().list(part='snippet', videoId=video_id).execute()
        items = resp.get('items', [])
        deleted = 0
        for item in items:
            if item['snippet'].get('trackKind') in ('asr', 'standard'):
                youtube.captions().delete(id=item['id']).execute()
                print(f'  Deleted caption track: {item["snippet"].get("name","auto")} ({item["snippet"]["trackKind"]})')
                deleted += 1
        if deleted:
            return
        if attempt < retries - 1:
            print(f'  No captions yet, waiting {wait}s... (attempt {attempt+1}/{retries})')
            time.sleep(wait)
    print('  No auto-generated captions found to delete.')


def set_thumbnail(creds, video_id: str, thumbnail_path: Path):
    from googleapiclient.discovery import build
    from googleapiclient.http import MediaFileUpload

    youtube  = build('youtube', 'v3', credentials=creds)
    media    = MediaFileUpload(str(thumbnail_path), mimetype='image/jpeg')
    youtube.thumbnails().set(videoId=video_id, media_body=media).execute()
    print(f'  Thumbnail set: {thumbnail_path.name}')


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--meta',    default=str(PIPELINE_META), help='pipeline_meta.json path')
    parser.add_argument('--video',   default=None,               help='Override video path')
    parser.add_argument('--title',   default=None,               help='Override title')
    parser.add_argument('--desc',    default=None,               help='Override description')
    parser.add_argument('--privacy', default='public',           help='public / unlisted / private')
    args = parser.parse_args()

    try:
        # ── Load metadata ──────────────────────────────────────────────
        meta = {}
        meta_path = Path(args.meta)
        if meta_path.exists():
            with open(meta_path, encoding='utf-8') as f:
                meta = json.load(f)

        title       = args.title or meta.get('title', 'Cyber Fraud Awareness | Banking Expert Ram')
        description = args.desc  or meta.get('description', '')
        tags        = meta.get('tags', ['cybersecurity', 'fraud', 'bankingexpertram'])
        if isinstance(tags, str):
            tags = [t.strip() for t in tags.split(',')]

        video_path = find_video(args.video)
        print(f'Video  : {video_path}')
        print(f'Title  : {title[:70]}')

        # ── Authenticate ───────────────────────────────────────────────
        print('Authenticating...')
        creds = get_credentials()
        print('  Auth OK')

        # ── Upload ─────────────────────────────────────────────────────
        result = upload_video(creds, video_path, title, description, tags,
                              privacy=args.privacy)

        # ── Set thumbnail ──────────────────────────────────────────────
        thumb = find_thumbnail(video_path)
        if thumb:
            try:
                set_thumbnail(creds, result['video_id'], thumb)
            except Exception as e:
                print(f'  Thumbnail warning: {e}')

        # ── Disable auto-generated captions ────────────────────────────
        print('  Disabling auto-generated captions...')
        try:
            disable_auto_captions(creds, result['video_id'])
        except Exception as e:
            print(f'  Caption warning: {e}')

        output = {'success': True, **result, 'title': title}
        print(json.dumps(output, ensure_ascii=False))

    except Exception as e:
        print(json.dumps({
            'success': False,
            'error':   str(e),
            'trace':   traceback.format_exc()[-500:],
        }, ensure_ascii=False))
        sys.exit(1)


if __name__ == '__main__':
    main()
