# MCP Servers — BankingExpertRam

MCP (Model Context Protocol) servers that extend the pipeline with Claude-native tool access.
These are isolated from the production pipeline — existing scripts are untouched.

## Servers

| Server | File | Purpose |
|---|---|---|
| youtube-mcp | `servers/youtube_mcp.py` | Upload videos, set thumbnails, fetch channel analytics |
| gdrive-mcp | `servers/gdrive_mcp.py` | Sync output_v19/ and script_editor.xlsx to Google Drive |

## Setup

### 1. Install dependencies
```bash
pip install mcp google-api-python-client google-auth-httplib2 google-auth-oauthlib
```

### 2. Google OAuth2 credentials
- Go to Google Cloud Console → APIs & Services → Credentials
- Create OAuth2 Client ID (Desktop app)
- Download JSON → save as `client_secrets.json` in project root
- Enable: YouTube Data API v3, Google Drive API

### 3. Add to .env
```
YOUTUBE_CLIENT_SECRETS_FILE=client_secrets.json
GDRIVE_FOLDER_ID=<your-drive-folder-id>
```
Get folder ID from Drive URL: `drive.google.com/drive/folders/<FOLDER_ID>`

### 4. Register with Claude Code
Add `configs/mcp_settings.json` contents to your `~/.claude/claude_desktop_config.json`
under the `mcpServers` key, with full absolute paths to the server scripts.

## First Run
Each server opens a browser for OAuth2 on first use. Tokens are cached in:
- `configs/youtube_token.json`
- `configs/gdrive_token.json`

These token files are gitignored — do not commit them.

## Usage with Claude Code
Once registered, Claude Code can call these tools directly in conversation:
- "Upload the latest video from output_v19/ to YouTube as unlisted"
- "Sync all MP4s to Drive folder"
- "Show me recent video analytics"
