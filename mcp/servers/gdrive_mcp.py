"""
Google Drive MCP Server for BankingExpertRam pipeline.
Syncs output_v19/ videos and Excel scripts to a designated Drive folder.

Setup:
    pip install mcp google-api-python-client google-auth-httplib2 google-auth-oauthlib
    Set GDRIVE_FOLDER_ID in .env with the target Drive folder ID.
"""

import os
import json
from pathlib import Path
from mcp.server import Server
from mcp.server.stdio import stdio_server
from mcp.types import Tool, TextContent
from googleapiclient.discovery import build
from googleapiclient.http import MediaFileUpload
from google_auth_oauthlib.flow import InstalledAppFlow
from google.auth.transport.requests import Request
from google.oauth2.credentials import Credentials

SCOPES = ["https://www.googleapis.com/auth/drive.file"]
TOKEN_FILE = Path(__file__).parent.parent / "configs" / "gdrive_token.json"
CLIENT_SECRETS = os.getenv("YOUTUBE_CLIENT_SECRETS_FILE", "client_secrets.json")
OUTPUT_DIR = Path(__file__).parent.parent.parent / "output_v19"
GDRIVE_FOLDER_ID = os.getenv("GDRIVE_FOLDER_ID", "")

server = Server("gdrive-mcp")


def get_drive_client():
    creds = None
    if TOKEN_FILE.exists():
        creds = Credentials.from_authorized_user_file(str(TOKEN_FILE), SCOPES)
    if not creds or not creds.valid:
        if creds and creds.expired and creds.refresh_token:
            creds.refresh(Request())
        else:
            flow = InstalledAppFlow.from_client_secrets_file(CLIENT_SECRETS, SCOPES)
            creds = flow.run_local_server(port=0)
        TOKEN_FILE.write_text(creds.to_json())
    return build("drive", "v3", credentials=creds)


@server.list_tools()
async def list_tools() -> list[Tool]:
    return [
        Tool(
            name="sync_output_videos",
            description="Upload all MP4 files from output_v19/ to the configured Google Drive folder.",
            inputSchema={
                "type": "object",
                "properties": {
                    "folder_id": {
                        "type": "string",
                        "description": "Drive folder ID to upload into (overrides GDRIVE_FOLDER_ID env var)"
                    }
                }
            }
        ),
        Tool(
            name="upload_script_excel",
            description="Upload the current script_editor.xlsx to Google Drive.",
            inputSchema={
                "type": "object",
                "properties": {
                    "folder_id": {"type": "string", "description": "Drive folder ID (optional)"}
                }
            }
        ),
        Tool(
            name="list_drive_files",
            description="List files in the configured Drive folder.",
            inputSchema={
                "type": "object",
                "properties": {
                    "folder_id": {"type": "string", "description": "Drive folder ID (optional)"}
                }
            }
        )
    ]


@server.call_tool()
async def call_tool(name: str, arguments: dict) -> list[TextContent]:
    drive = get_drive_client()
    folder_id = arguments.get("folder_id") or GDRIVE_FOLDER_ID

    if not folder_id:
        return [TextContent(type="text", text="Error: GDRIVE_FOLDER_ID not set. Pass folder_id or set the env var.")]

    if name == "sync_output_videos":
        mp4_files = list(OUTPUT_DIR.glob("*.mp4"))
        if not mp4_files:
            return [TextContent(type="text", text="No MP4 files found in output_v19/.")]
        results = []
        for mp4 in mp4_files:
            meta = {"name": mp4.name, "parents": [folder_id]}
            media = MediaFileUpload(str(mp4), mimetype="video/mp4", resumable=True)
            file = drive.files().create(body=meta, media_body=media, fields="id,name").execute()
            results.append(f"Uploaded: {file['name']} (ID: {file['id']})")
        return [TextContent(type="text", text="\n".join(results))]

    elif name == "upload_script_excel":
        excel_path = OUTPUT_DIR.parent / "script_editor.xlsx"
        if not excel_path.exists():
            return [TextContent(type="text", text="script_editor.xlsx not found.")]
        meta = {"name": "script_editor.xlsx", "parents": [folder_id]}
        mime = "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
        media = MediaFileUpload(str(excel_path), mimetype=mime)
        file = drive.files().create(body=meta, media_body=media, fields="id,name").execute()
        return [TextContent(type="text", text=f"Uploaded script_editor.xlsx (ID: {file['id']})")]

    elif name == "list_drive_files":
        resp = drive.files().list(
            q=f"'{folder_id}' in parents and trashed=false",
            fields="files(id, name, mimeType, modifiedTime)"
        ).execute()
        files = resp.get("files", [])
        if not files:
            return [TextContent(type="text", text="No files in this folder.")]
        lines = [f"- {f['name']} ({f['mimeType']}) modified:{f['modifiedTime']}" for f in files]
        return [TextContent(type="text", text="\n".join(lines))]

    return [TextContent(type="text", text=f"Unknown tool: {name}")]


if __name__ == "__main__":
    import asyncio

    async def main():
        async with stdio_server() as (read_stream, write_stream):
            await server.run(read_stream, write_stream, server.create_initialization_options())

    asyncio.run(main())
