"""
YouTube MCP Server for BankingExpertRam pipeline.
Handles video upload, metadata setting, and analytics fetch via YouTube Data API v3.

Setup:
    pip install mcp google-api-python-client google-auth-httplib2 google-auth-oauthlib
    Set YOUTUBE_CLIENT_SECRETS_FILE in .env pointing to your OAuth2 credentials JSON.
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

SCOPES = ["https://www.googleapis.com/auth/youtube.upload",
          "https://www.googleapis.com/auth/youtube.readonly"]
TOKEN_FILE = Path(__file__).parent.parent / "configs" / "youtube_token.json"
CLIENT_SECRETS = os.getenv("YOUTUBE_CLIENT_SECRETS_FILE", "client_secrets.json")

server = Server("youtube-mcp")


def get_youtube_client():
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
    return build("youtube", "v3", credentials=creds)


@server.list_tools()
async def list_tools() -> list[Tool]:
    return [
        Tool(
            name="upload_video",
            description="Upload a video file to the BankingExpertRam YouTube channel with title, description, and tags.",
            inputSchema={
                "type": "object",
                "properties": {
                    "video_path": {"type": "string", "description": "Absolute path to the MP4 file"},
                    "title": {"type": "string", "description": "Video title (Hindi OK)"},
                    "description": {"type": "string", "description": "Video description"},
                    "tags": {"type": "array", "items": {"type": "string"}, "description": "Tag list"},
                    "category_id": {"type": "string", "default": "28", "description": "YouTube category ID (28=Science & Tech)"},
                    "privacy": {"type": "string", "enum": ["public", "unlisted", "private"], "default": "private"}
                },
                "required": ["video_path", "title", "description"]
            }
        ),
        Tool(
            name="get_channel_analytics",
            description="Fetch recent video analytics (views, likes, comments) for the channel.",
            inputSchema={
                "type": "object",
                "properties": {
                    "max_results": {"type": "integer", "default": 5, "description": "Number of recent videos to fetch"}
                }
            }
        ),
        Tool(
            name="set_thumbnail",
            description="Set a custom thumbnail for an already-uploaded video.",
            inputSchema={
                "type": "object",
                "properties": {
                    "video_id": {"type": "string", "description": "YouTube video ID"},
                    "thumbnail_path": {"type": "string", "description": "Absolute path to thumbnail image (JPG/PNG)"}
                },
                "required": ["video_id", "thumbnail_path"]
            }
        )
    ]


@server.call_tool()
async def call_tool(name: str, arguments: dict) -> list[TextContent]:
    youtube = get_youtube_client()

    if name == "upload_video":
        video_path = arguments["video_path"]
        if not Path(video_path).exists():
            return [TextContent(type="text", text=f"Error: file not found: {video_path}")]

        body = {
            "snippet": {
                "title": arguments["title"],
                "description": arguments["description"],
                "tags": arguments.get("tags", []),
                "categoryId": arguments.get("category_id", "28")
            },
            "status": {
                "privacyStatus": arguments.get("privacy", "private")
            }
        }
        media = MediaFileUpload(video_path, chunksize=-1, resumable=True, mimetype="video/mp4")
        request = youtube.videos().insert(part="snippet,status", body=body, media_body=media)
        response = request.execute()
        video_id = response["id"]
        return [TextContent(type="text", text=f"Uploaded successfully. Video ID: {video_id}\nURL: https://youtu.be/{video_id}")]

    elif name == "get_channel_analytics":
        max_results = arguments.get("max_results", 5)
        resp = youtube.search().list(part="snippet", forMine=True, type="video",
                                     order="date", maxResults=max_results).execute()
        items = resp.get("items", [])
        lines = []
        for item in items:
            vid_id = item["id"]["videoId"]
            title = item["snippet"]["title"]
            published = item["snippet"]["publishedAt"]
            lines.append(f"- [{title}] ID:{vid_id} Published:{published}")
        return [TextContent(type="text", text="\n".join(lines) if lines else "No videos found.")]

    elif name == "set_thumbnail":
        video_id = arguments["video_id"]
        thumb_path = arguments["thumbnail_path"]
        if not Path(thumb_path).exists():
            return [TextContent(type="text", text=f"Error: thumbnail not found: {thumb_path}")]
        media = MediaFileUpload(thumb_path)
        youtube.thumbnails().set(videoId=video_id, media_body=media).execute()
        return [TextContent(type="text", text=f"Thumbnail set for video {video_id}.")]

    return [TextContent(type="text", text=f"Unknown tool: {name}")]


if __name__ == "__main__":
    import asyncio

    async def main():
        async with stdio_server() as (read_stream, write_stream):
            await server.run(read_stream, write_stream, server.create_initialization_options())

    asyncio.run(main())
