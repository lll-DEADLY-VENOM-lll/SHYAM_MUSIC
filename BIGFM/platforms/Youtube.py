import asyncio
import os
import re
import random
from typing import Union
import yt_dlp
from pyrogram.enums import MessageEntityType
from pyrogram.types import Message
from googleapiclient.discovery import build 
from googleapiclient.errors import HttpError
import config 

API_KEYS = [k.strip() for k in config.API_KEY.split(",")]
API_INDEX = 0 

def get_youtube_client():
    global API_INDEX
    return build("youtube", "v3", developerKey=API_KEYS[API_INDEX], static_discovery=False)

class YouTubeAPI:
    def __init__(self):
        self.base = "https://www.youtube.com/watch?v="
        self.regex = r"(?:youtube\.com|youtu\.be)"

    def parse_duration(self, duration):
        match = re.search(r'PT(?:(\d+)H)?(?:(\d+)M)?(?:(\d+)S)?', duration)
        hours = int(match.group(1) or 0)
        minutes = int(match.group(2) or 0)
        seconds = int(match.group(3) or 0)
        total_seconds = hours * 3600 + minutes * 60 + seconds
        duration_str = f"{hours:02d}:{minutes:02d}:{seconds:02d}" if hours > 0 else f"{minutes:02d}:{seconds:02d}"
        return duration_str, total_seconds

    async def details(self, link: str, videoid: Union[bool, str] = None):
        global API_INDEX
        if videoid: vidid = link
        else:
            match = re.search(r"(?:v=|\/)([0-9A-Za-z_-]{11})", link)
            vidid = match.group(1) if match else None
        
        for _ in range(len(API_KEYS)):
            youtube = get_youtube_client() 
            try:
                if not vidid:
                    res = await asyncio.to_thread(youtube.search().list(q=link, part="id", maxResults=1, type="video").execute)
                    if not res.get("items"): return None
                    vidid = res["items"][0]["id"]["videoId"]
                
                res = await asyncio.to_thread(youtube.videos().list(part="snippet,contentDetails", id=vidid).execute)
                if not res.get("items"): return None
                item = res["items"][0]
                title, (d_min, d_sec) = item["snippet"]["title"], self.parse_duration(item["contentDetails"]["duration"])
                return title, d_min, d_sec, item["snippet"]["thumbnails"]["high"]["url"], vidid
            except HttpError as e:
                if e.resp.status in [403, 429]:
                    API_INDEX = (API_INDEX + 1) % len(API_KEYS)
                    continue 
                return None
        return None

    async def download(self, link: str, mystic, video=None, videoid=None, songaudio=None, songvideo=None, format_id=None, title=None) -> str:
        if videoid: link = self.base + link
        loop = asyncio.get_running_loop()

        # BYPASS OPTIONS: Android aur iOS client use karke YouTube ko dhokha dena
        ytdl_opts = {
            "quiet": True,
            "no_warnings": True,
            "geo_bypass": True,
            "nocheckcertificate": True,
            "outtmpl": "downloads/%(id)s.%(ext)s",
            "user_agent": "Mozilla/5.0 (iPhone; CPU iPhone OS 17_0 like Mac OS X) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/17.0 Mobile/15E148 Safari/604.1",
            "extractor_args": {
                "youtube": {
                    "player_client": ["ios", "android"], # Android/iOS clients are harder to block
                    "player_skip": ["webpage", "configs"],
                }
            },
        }

        if songvideo:
            ytdl_opts.update({"format": f"{format_id}+140", "outtmpl": f"downloads/{title}", "merge_output_format": "mp4"})
        elif songaudio:
            ytdl_opts.update({"format": "bestaudio/best", "outtmpl": f"downloads/{title}.%(ext)s", "postprocessors": [{"key": "FFmpegExtractAudio", "preferredcodec": "mp3", "preferredquality": "192"}]})

        try:
            def dl():
                with yt_dlp.YoutubeDL(ytdl_opts) as ydl:
                    info = ydl.extract_info(link, download=True)
                    return ydl.prepare_filename(info)

            downloaded_file = await loop.run_in_executor(None, dl)
            return downloaded_file, True
        except Exception as e:
            print(f"Download Error: {e}")
            return None, False

# Important: Is line ko mat hatana
cookies = None
