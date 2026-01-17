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
    # Agar config se nahi milta toh default list (security ke liye)
    YOUTUBE_API_KEYS = ["AIzaSyACgEYXqRtQZ8AG77T5xZgGtEP1bt8Mekk"]

class YouTubeAPI:
    # --- GLOBAL STATE (Bot restart hone tak yaad rahega) ---
    current_key_index = 0
    youtube_client = None

    def __init__(self):
        self.base = "https://www.youtube.com/watch?v="
        self.regex = r"(?:youtube\.com|youtu\.be)"
        self.listbase = "https://youtube.com/playlist?list="
        
        # Client initialize karein agar nahi hai toh
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
        """Quota khatm hone par agli key par permanent shift karein"""
        if len(YOUTUBE_API_KEYS) > 1:
            YouTubeAPI.current_key_index = (YouTubeAPI.current_key_index + 1) % len(YOUTUBE_API_KEYS)
            self._build_youtube_client()
            print(f"INFO: Quota Full. Switched to Key Index: {YouTubeAPI.current_key_index}")
        else:
            print("ERROR: No more API keys available for rotation.")

    async def url(self, message_1: Message) -> Union[str, None]:
        """Message se YouTube URL nikalne ke liye (Missing Function)"""
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

    def parse_duration(self, duration):
        """ISO 8601 duration ko MM:SS mein badalta hai"""
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

        # Google API se koshish karein
        if YouTubeAPI.youtube_client:
            for _ in range(len(YOUTUBE_API_KEYS)):
                try:
                    if not vidid:
                        search_response = await asyncio.to_thread(
                            YouTubeAPI.youtube_client.search().list(q=link, part="id", maxResults=1, type="video").execute
                        )
                        if not search_response.get("items"): break
                        vidid = search_response["items"][0]["id"]["videoId"]

                    video_response = await asyncio.to_thread(
                        YouTubeAPI.youtube_client.videos().list(part="snippet,contentDetails", id=vidid).execute
                    )
                    
                    if not video_response.get("items"): break

                    video_data = video_response["items"][0]
                    title = video_data["snippet"]["title"]
                    thumbnail = video_data["snippet"]["thumbnails"]["high"]["url"]
                    duration_iso = video_data["contentDetails"]["duration"]
                    duration_min, duration_sec = self.parse_duration(duration_iso)
                    
                    return title, duration_min, duration_sec, thumbnail, vidid

                except HttpError as e:
                    if e.resp.status in [403, 429]: # Quota limit
                        self._rotate_key()
                        continue
                    break
                except Exception:
                    break

        # Fallback: Agar API fail ho jaye toh yt-dlp use karein
        try:
            loop = asyncio.get_running_loop()
            with yt_dlp.YoutubeDL({"quiet": True}) as ydl:
                info = await loop.run_in_executor(None, lambda: ydl.extract_info(link if not vidid else self.base + vidid, download=False))
                if 'entries' in info: info = info['entries'][0]
                return info['title'], info.get('duration_string', "00:00"), info.get('duration', 0), info['thumbnail'], info['id']
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
        track_details = {
            "title": title,
            "link": self.base + vidid,
            "vidid": vidid,
            "duration_min": duration_min,
            "thumb": thumbnail,
        }
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
            opts = {"format": "bestaudio/best" if not video else "best[height<=?720][ext=mp4]", "outtmpl": "downloads/%(id)s.%(ext)s", "quiet": True}
            with yt_dlp.YoutubeDL(opts) as ydl:
                info = ydl.extract_info(link, download=True)
                return os.path.join("downloads", f"{info['id']}.{info['ext']}")
        return await loop.run_in_executor(None, dl), True
