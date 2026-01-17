import asyncio
import os
import re
from typing import Union

import yt_dlp
from pyrogram.enums import MessageEntityType
from pyrogram.types import Message
from googleapiclient.discovery import build
from googleapiclient.errors import HttpError

# Config se API Keys ki list
try:
    from config import YOUTUBE_API_KEYS
except ImportError:
    YOUTUBE_API_KEYS = []

class YouTubeAPI:
    # --- GLOBAL STATE ---
    current_key_index = 0
    youtube_client = None

    def __init__(self):
        self.base = "https://www.youtube.com/watch?v="
        self.regex = r"(?:youtube\.com|youtu\.be)"
        self.listbase = "https://youtube.com/playlist?list="
        
        if YouTubeAPI.youtube_client is None:
            self._build_youtube_client()

    async def url(self, message_1: Message) -> Union[str, None]:
        messages = [message_1]
        if message_1.reply_to_message:
            messages.append(message_1.reply_to_message)
        
        for message in messages:
            if message.entities:
                for entity in message.entities:
                    if entity.type == MessageEntityType.URL:
                        text = message.text or message.caption
                        return text[entity.offset : entity.offset + entity.length]
            if message.caption_entities:
                for entity in message.caption_entities:
                    if entity.type == MessageEntityType.TEXT_LINK:
                        return entity.url
        return None

    def _build_youtube_client(self):
        if not YOUTUBE_API_KEYS:
            return None
        try:
            YouTubeAPI.youtube_client = build(
                "youtube", 
                "v3", 
                developerKey=YOUTUBE_API_KEYS[YouTubeAPI.current_key_index], 
                static_discovery=False
            )
        except Exception:
            YouTubeAPI.youtube_client = None

    def _rotate_key(self):
        if len(YOUTUBE_API_KEYS) > 1:
            YouTubeAPI.current_key_index = (YouTubeAPI.current_key_index + 1) % len(YOUTUBE_API_KEYS)
            self._build_youtube_client()

    def parse_duration(self, duration):
        match = re.search(r'PT(?:(\d+)H)?(?:(\d+)M)?(?:(\d+)S)?', duration)
        hours = int(match.group(1) or 0)
        minutes = int(match.group(2) or 0)
        seconds = int(match.group(3) or 0)
        total_seconds = hours * 3600 + minutes * 60 + seconds
        duration_str = f"{hours:02d}:{minutes:02d}:{seconds:02d}" if hours > 0 else f"{minutes:02d}:{seconds:02d}"
        return duration_str, total_seconds

    async def details(self, link: str, videoid: Union[bool, str] = None):
        if videoid:
            vidid = link
        else:
            match = re.search(r"(?:v=|\/)([0-9A-Za-z_-]{11})", link)
            vidid = match.group(1) if match else None

        # --- GOOGLE API TRY ---
        if YouTubeAPI.youtube_client:
            for _ in range(len(YOUTUBE_API_KEYS)):
                try:
                    if not vidid:
                        search_res = await asyncio.to_thread(
                            YouTubeAPI.youtube_client.search().list(q=link, part="id", maxResults=1, type="video").execute
                        )
                        if not search_res.get("items"): break
                        vidid = search_res["items"][0]["id"]["videoId"]

                    video_res = await asyncio.to_thread(
                        YouTubeAPI.youtube_client.videos().list(part="snippet,contentDetails", id=vidid).execute
                    )
                    
                    if not video_res.get("items"): break
                    v_data = video_res["items"][0]
                    title = v_data["snippet"]["title"]
                    thumbnail = v_data["snippet"]["thumbnails"]["high"]["url"]
                    duration_min, _ = self.parse_duration(v_data["contentDetails"]["duration"])
                    
                    return title, duration_min, 0, thumbnail, vidid
                except HttpError as e:
                    if e.resp.status in [403, 429]:
                        self._rotate_key()
                        continue
                    break
                except Exception: break

        # --- YT-DLP FALLBACK (Optimized for SABR/No-JS) ---
        try:
            loop = asyncio.get_running_loop()
            search_query = f"ytsearch1:{link}" if not vidid else f"https://www.youtube.com/watch?v={vidid}"
            
            # YDL Options to minimize JS runtime errors
            ydl_opts = {
                "quiet": True,
                "no_warnings": True,
                "format": "bestaudio/best",
                "skip_download": True,
                "nocheckcertificate": True,
                "geo_bypass": True,
                "extract_flat": "in_playlist", # SABR errors se bachne ke liye
            }
            
            with yt_dlp.YoutubeDL(ydl_opts) as ydl:
                info = await loop.run_in_executor(None, lambda: ydl.extract_info(search_query, download=False))
                if 'entries' in info and len(info['entries']) > 0:
                    data = info['entries'][0]
                else:
                    data = info

                return (
                    data.get('title', 'Unknown'),
                    data.get('duration_string', '00:00'),
                    data.get('duration', 0),
                    data.get('thumbnail', ''),
                    data.get('id', '')
                )
        except Exception:
            return None

    async def title(self, link: str, videoid: Union[bool, str] = None):
        res = await self.details(link, videoid)
        return res[0] if res else "Unknown"

    async def duration(self, link: str, videoid: Union[bool, str] = None):
        res = await self.details(link, videoid)
        return res[1] if res else "00:00"

    async def thumbnail(self, link: str, videoid: Union[bool, str] = None):
        res = await self.details(link, videoid)
        return res[3] if res else None

    async def track(self, link: str, videoid: Union[bool, str] = None):
        res = await self.details(link, videoid)
        if not res: return None, None
        title, duration_min, duration_sec, thumbnail, vidid = res
        track_details = {"title": title, "link": self.base + vidid, "vidid": vidid, "duration_min": duration_min, "thumb": thumbnail}
        return track_details, vidid

    async def exists(self, link: str, videoid: Union[bool, str] = None):
        if videoid: link = self.base + link
        return bool(re.search(self.regex, link))

    async def video(self, link: str, videoid: Union[bool, str] = None):
        if videoid: link = self.base + link
        opts = ["yt-dlp", "-g", "-f", "best[height<=?720][ext=mp4]/best", "--geo-bypass", "--no-playlist", f"{link}"]
        proc = await asyncio.create_subprocess_exec(*opts, stdout=asyncio.subprocess.PIPE, stderr=asyncio.subprocess.PIPE)
        stdout, _ = await proc.communicate()
        return (1, stdout.decode().split("\n")[0]) if stdout else (0, "Error")

    async def download(self, link, mystic, video=None, videoid=None, songaudio=None, songvideo=None, format_id=None, title=None):
        if videoid: link = self.base + link
        loop = asyncio.get_running_loop()
        def dl():
            opts = {"format": "bestaudio/best" if not video else "best[height<=?720][ext=mp4]", "outtmpl": "downloads/%(id)s.%(ext)s", "quiet": True, "no_warnings": True}
            with yt_dlp.YoutubeDL(opts) as ydl:
                info = ydl.extract_info(link, download=True)
                return os.path.join("downloads", f"{info['id']}.{info['ext']}")
        return await loop.run_in_executor(None, dl), True
