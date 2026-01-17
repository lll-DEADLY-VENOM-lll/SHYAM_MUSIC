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
    # --- GLOBAL STATE ---
    current_key_index = 0
    youtube_client = None

    def __init__(self):
        self.base = "https://www.youtube.com/watch?v="
        self.regex = r"(?:youtube\.com|youtu\.be)"
        self.listbase = "https://youtube.com/playlist?list="
        
        # Initialize client if not already done
        if YouTubeAPI.youtube_client is None:
            self._build_youtube_client()

    def _build_youtube_client(self):
        """Current index wali key se client build karta hai"""
        if not YOUTUBE_API_KEYS:
            print("ERROR: No API Keys found in config!")
            return None
        
        try:
            YouTubeAPI.youtube_client = build(
                "youtube", 
                "v3", 
                developerKey=YOUTUBE_API_KEYS[YouTubeAPI.current_key_index], 
                static_discovery=False
            )
            print(f"SUCCESS: YouTube Client built with Key Index {YouTubeAPI.current_key_index}")
        except Exception as e:
            print(f"ERROR Building Client: {e}")
            YouTubeAPI.youtube_client = None

    def _rotate_key(self):
        """Jab quota khatm ho jaye toh permanent agli key par switch karein"""
        if len(YOUTUBE_API_KEYS) > 1:
            YouTubeAPI.current_key_index = (YouTubeAPI.current_key_index + 1) % len(YOUTUBE_API_KEYS)
            self._build_youtube_client()
            print(f"SWITCH: Moved to Key Index {YouTubeAPI.current_key_index}")
        else:
            print("ERROR: No more keys available to rotate!")

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

        # Agar API Keys available hain
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
                    duration_min, _ = self.parse_duration(duration_iso)
                    
                    return title, duration_min, 0, thumbnail, vidid

                except HttpError as e:
                    if e.resp.status in [403, 429]:
                        print(f"QUOTA EXCEEDED for Key {YouTubeAPI.current_key_index}")
                        self._rotate_key()
                        continue
                    break
                except Exception as e:
                    print(f"API Error: {e}")
                    break

        # --- FALLBACK: Agar API fail ho jaye toh yt-dlp use karein ---
        print("FALLBACK: Using yt-dlp for details...")
        try:
            loop = asyncio.get_running_loop()
            info = await loop.run_in_executor(None, lambda: yt_dlp.YoutubeDL({"quiet": True, "no_warnings": True}).extract_info(link if not vidid else self.base + vidid, download=False))
            
            if 'entries' in info: # Agar playlist hai toh pehla item
                info = info['entries'][0]
                
            return info['title'], info.get('duration_string', "00:00"), info['duration'], info['thumbnail'], info['id']
        except Exception as e:
            print(f"Fallback Error: {e}")
            return None

    # In functions ko details() use karne ke liye fix kiya
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

    # ... Baaki functions (video, download, playlist) same rahenge ...
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
