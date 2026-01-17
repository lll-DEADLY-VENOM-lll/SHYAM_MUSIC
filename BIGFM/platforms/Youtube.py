import asyncio
import os
import re
from typing import Union

import yt_dlp
from pyrogram.enums import MessageEntityType
from pyrogram.types import Message
from googleapiclient.discovery import build
from googleapiclient.errors import HttpError

# Config se API Keys ki list mangwa rahe hain
try:
    from config import YOUTUBE_API_KEYS
except ImportError:
    YOUTUBE_API_KEYS = []

class YouTubeAPI:
    # --- GLOBAL STATE (Bot restart hone tak yaad rahega) ---
    current_key_index = 0
    youtube_client = None

    def __init__(self):
        self.base = "https://www.youtube.com/watch?v="
        self.regex = r"(?:youtube\.com|youtu\.be)"
        self.listbase = "https://youtube.com/playlist?list="
        
        # Client initialize karein agar pehli baar hai
        if YouTubeAPI.youtube_client is None:
            self._build_youtube_client()

    def _build_youtube_client(self):
        """Current active key se Google API client banata hai"""
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
        """Quota khatm hone par permanent switch karein"""
        if len(YOUTUBE_API_KEYS) > 1:
            YouTubeAPI.current_key_index = (YouTubeAPI.current_key_index + 1) % len(YOUTUBE_API_KEYS)
            self._build_youtube_client()
            print(f"INFO: Quota Full. Switched to Key Index: {YouTubeAPI.current_key_index}")

    def format_seconds(self, seconds):
        """Seconds (int) ko MM:SS format mein badalta hai"""
        if not seconds:
            return "00:00"
        seconds = int(seconds)
        minutes, seconds = divmod(seconds, 60)
        hours, minutes = divmod(minutes, 60)
        if hours > 0:
            return f"{hours:02d}:{minutes:02d}:{seconds:02d}"
        return f"{minutes:02d}:{seconds:02d}"

    def parse_iso_duration(self, duration_iso):
        """ISO 8601 (PT4M13S) ko format karta hai"""
        match = re.search(r'PT(?:(\d+)H)?(?:(\d+)M)?(?:(\d+)S)?', duration_iso)
        hours = int(match.group(1) or 0)
        minutes = int(match.group(2) or 0)
        seconds = int(match.group(3) or 0)
        total_sec = hours * 3600 + minutes * 60 + seconds
        return self.format_seconds(total_sec), total_sec

    async def url(self, message: Message) -> Union[str, None]:
        messages = [message]
        if message.reply_to_message:
            messages.append(message.reply_to_message)
        for m in messages:
            if m.entities:
                for entity in m.entities:
                    if entity.type == MessageEntityType.URL:
                        text = m.text or m.caption
                        return text[entity.offset : entity.offset + entity.length]
            if m.caption_entities:
                for entity in m.caption_entities:
                    if entity.type == MessageEntityType.TEXT_LINK:
                        return entity.url
        return None

    async def details(self, link: str, videoid: Union[bool, str] = None):
        if videoid:
            vidid = link
        else:
            match = re.search(r"(?:v=|\/)([0-9A-Za-z_-]{11})", link)
            vidid = match.group(1) if match else None

        # --- 1. GOOGLE API ATTEMPT ---
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
                    
                    data = video_res["items"][0]
                    title = data["snippet"]["title"]
                    thumb = data["snippet"]["thumbnails"]["high"]["url"]
                    duration_min, duration_sec = self.parse_iso_duration(data["contentDetails"]["duration"])
                    
                    return title, duration_min, duration_sec, thumb, vidid

                except HttpError as e:
                    if e.resp.status in [403, 429]:
                        self._rotate_key()
                        continue
                    break
                except Exception: break

        # --- 2. YT-DLP FALLBACK (If API Fails) ---
        try:
            loop = asyncio.get_running_loop()
            query = f"ytsearch1:{link}" if not vidid else f"https://www.youtube.com/watch?v={vidid}"
            
            ydl_opts = {
                "quiet": True,
                "no_warnings": True,
                "format": "bestaudio/best",
                "skip_download": True,
                "nocheckcertificate": True,
            }
            
            with yt_dlp.YoutubeDL(ydl_opts) as ydl:
                info = await loop.run_in_executor(None, lambda: ydl.extract_info(query, download=False))
                if 'entries' in info:
                    info = info['entries'][0]
                
                title = info.get('title', 'Unknown Title')
                vid_id = info.get('id', '')
                thumb = info.get('thumbnail', '')
                
                # Proper Duration Logic
                duration_sec = info.get('duration', 0)
                duration_min = self.format_seconds(duration_sec)

                return title, duration_min, duration_sec, thumb, vid_id
        except Exception as e:
            print(f"Extraction Error: {e}")
            return None

    # Helper functions details() call karenge taaki format sahi rahe
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
        title, d_min, d_sec, thumb, vidid = res
        track_details = {"title": title, "link": self.base + vidid, "vidid": vidid, "duration_min": d_min, "thumb": thumb}
        return track_details, vidid

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
            opts = {"format": "bestaudio/best" if not video else "best[height<=?720][ext=mp4]", "outtmpl": "downloads/%(id)s.%(ext)s", "quiet": True}
            with yt_dlp.YoutubeDL(opts) as ydl:
                info = ydl.extract_info(link, download=True)
                return os.path.join("downloads", f"{info['id']}.{info['ext']}")
        return await loop.run_in_executor(None, dl), True
