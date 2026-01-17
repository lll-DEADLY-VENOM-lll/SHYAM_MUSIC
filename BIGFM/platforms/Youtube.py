import asyncio, os, re, glob, random
import yt_dlp
from typing import Union
from pyrogram.types import Message
from pyrogram.enums import MessageEntityType
from googleapiclient.discovery import build
import isodate # YouTube duration (PT1M2S) को कन्वर्ट करने के लिए

# अपनी API Key यहाँ डालें
YOUTUBE_API_KEY = "YOUR_GOOGLE_API_KEY_HERE"

# YouTube API Client Setup
youtube_client = build("youtube", "v3", developerKey=YOUTUBE_API_KEY)

def time_to_seconds(time):
    # ISO 8601 duration को seconds में बदलने के लिए
    return int(isodate.parse_duration(time).total_seconds())

def format_duration(seconds):
    minutes, seconds = divmod(seconds, 60)
    hours, minutes = divmod(minutes, 60)
    if hours > 0:
        return f"{hours:02d}:{minutes:02d}:{seconds:02d}"
    return f"{minutes:02d}:{seconds:02d}"

class YouTubeAPI:
    def __init__(self):
        self.base = "https://www.youtube.com/watch?v="
        self.regex = r"(?:youtube\.com|youtu\.be)"
        self.listbase = "https://youtube.com/playlist?list="

    async def get_video_id(self, link: str):
        # लिंक से Video ID निकालने के लिए
        regex = r"(?:v=|\/)([0-9A-Za-z_-]{11}).*"
        match = re.search(regex, link)
        return match.group(1) if match else None

    async def fetch_details(self, query: str, is_id=False):
        """Google API के ज़रिए डेटा लाना"""
        loop = asyncio.get_event_loop()
        if not is_id:
            # अगर Query है तो सर्च करें
            search_request = await loop.run_in_executor(None, lambda: youtube_client.search().list(
                q=query, part="id", maxResults=1, type="video"
            ).execute())
            if not search_request.get("items"):
                return None
            video_id = search_request["items"][0]["id"]["videoId"]
        else:
            video_id = query

        # वीडियो की पूरी जानकारी लें
        video_request = await loop.run_in_executor(None, lambda: youtube_client.videos().list(
            id=video_id, part="snippet,contentDetails"
        ).execute())

        if not video_request.get("items"):
            return None

        item = video_request["items"][0]
        title = item["snippet"]["title"]
        duration_iso = item["contentDetails"]["duration"]
        duration_sec = time_to_seconds(duration_iso)
        duration_min = format_duration(duration_sec)
        thumbnail = item["snippet"]["thumbnails"]["high"]["url"]
        
        return {
            "title": title,
            "duration_min": duration_min,
            "duration_sec": duration_sec,
            "thumbnail": thumbnail,
            "id": video_id,
            "link": self.base + video_id
        }

    async def details(self, link: str, videoid: Union[bool, str] = None):
        if videoid:
            v_id = link
        else:
            v_id = await self.get_video_id(link)
        
        data = await self.fetch_details(v_id or link, is_id=True if v_id else False)
        return data["title"], data["duration_min"], data["duration_sec"], data["thumbnail"], data["id"]

    async def title(self, link: str, videoid: Union[bool, str] = None):
        res = await self.details(link, videoid)
        return res[0]

    async def duration(self, link: str, videoid: Union[bool, str] = None):
        res = await self.details(link, videoid)
        return res[1]

    async def track(self, link: str, videoid: Union[bool, str] = None):
        if videoid:
            v_id = link
        else:
            v_id = await self.get_video_id(link)
            
        data = await self.fetch_details(v_id or link, is_id=True if v_id else False)
        track_details = {
            "title": data["title"],
            "link": data["link"],
            "vidid": data["id"],
            "duration_min": data["duration_min"],
            "thumb": data["thumbnail"],
        }
        return track_details, data["id"]

    async def download(
        self,
        link: str,
        mystic,
        video: Union[bool, str] = None,
        videoid: Union[bool, str] = None,
        songaudio: Union[bool, str] = None,
        songvideo: Union[bool, str] = None,
        format_id: Union[bool, str] = None,
        title: Union[bool, str] = None,
    ) -> str:
        if videoid:
            link = self.base + link
        loop = asyncio.get_running_loop()

        # yt-dlp options with cookies to avoid 403/IP Ban during download
        common_opts = {
            "quiet": True,
            "no_warnings": True,
            "geo_bypass": True,
            "nocheckcertificate": True,
            "cookiefile": "cookies.txt" if os.path.exists("cookies.txt") else None, # अगर cookies हैं
        }

        def download_logic():
            if songvideo:
                opts = {**common_opts, "format": f"{format_id}+140", "outtmpl": f"downloads/{title}.mp4", "merge_output_format": "mp4"}
            elif songaudio:
                opts = {**common_opts, "format": format_id, "outtmpl": f"downloads/{title}.%(ext)s", 
                        "postprocessors": [{"key": "FFmpegExtractAudio", "preferredcodec": "mp3", "preferredquality": "192"}]}
            elif video:
                opts = {**common_opts, "format": "bestvideo[height<=720]+bestaudio/best", "outtmpl": "downloads/%(id)s.%(ext)s"}
            else:
                opts = {**common_opts, "format": "bestaudio/best", "outtmpl": "downloads/%(id)s.%(ext)s"}

            with yt_dlp.YoutubeDL(opts) as ydl:
                info = ydl.extract_info(link, download=True)
                return ydl.prepare_filename(info)

        file_path = await loop.run_in_executor(None, download_logic)
        return file_path, None
