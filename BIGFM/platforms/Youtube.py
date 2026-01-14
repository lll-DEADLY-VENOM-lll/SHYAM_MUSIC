import asyncio
import os
import re
from typing import Union

import yt_dlp
from pyrogram.enums import MessageEntityType
from pyrogram.types import Message
from googleapiclient.discovery import build
from googleapiclient.errors import HttpError

from BIGFM.utils.formatters import time_to_seconds

# --- CONFIGURATION ---
API_KEYS = [
    "AIzaSyAfG6kmGSSS0p2NM5nrMoGlhxit1whQvPk", # Pehli Key
    "AIzaSyCJhc8D6CB0Ir35aBPNq7IVxO_Hl-R1YT0", # Dusri Key
    "AIzaSyD2xyghITQnJfohRzCoRzhYUH_HYAYINGM"  # Teesri Key
]

# Cookies handling for yt-dlp
cookies_file = "BIGFM/cookies.txt"
if not os.path.exists(cookies_file):
    cookies_file = None

async def shell_cmd(cmd):
    proc = await asyncio.create_subprocess_shell(
        cmd,
        stdout=asyncio.subprocess.PIPE,
        stderr=asyncio.subprocess.PIPE,
    )
    out, errorz = await proc.communicate()
    if errorz:
        if "unavailable videos are hidden" in (errorz.decode("utf-8")).lower():
            return out.decode("utf-8")
        else:
            return errorz.decode("utf-8")
    return out.decode("utf-8")

class YouTubeAPI:
    def __init__(self):
        self.base = "https://www.youtube.com/watch?v="
        self.regex = r"(?:youtube\.com|youtu\.be)"
        self.listbase = "https://youtube.com/playlist?list="
        self.key_index = 0  

    def get_service(self):
        """Builds service with cache_discovery=False to fix file_cache warning"""
        return build(
            "youtube", 
            "v3", 
            developerKey=API_KEYS[self.key_index],
            cache_discovery=False  # <--- Yeh line Error fix karegi
        )

    async def call_api(self, resource, method, **kwargs):
        attempts = 0
        while attempts < len(API_KEYS):
            try:
                service = self.get_service()
                if resource == "search":
                    return await asyncio.to_thread(service.search().list(**kwargs).execute)
                elif resource == "videos":
                    return await asyncio.to_thread(service.videos().list(**kwargs).execute)
                
            except HttpError as e:
                # Quota limit check
                if e.resp.status == 403 and "quotaExceeded" in str(e):
                    self.key_index = (self.key_index + 1) % len(API_KEYS)
                    print(f"⚠️ Quota Exceeded! Switching to API Key {self.key_index + 1}")
                    attempts += 1
                    continue
                else:
                    raise e
        return None

    def parse_duration(self, duration):
        match = re.search(r'PT(?:(\d+)H)?(?:(\d+)M)?(?:(\d+)S)?', duration)
        hours = int(match.group(1) or 0)
        minutes = int(match.group(2) or 0)
        seconds = int(match.group(3) or 0)
        total_seconds = hours * 3600 + minutes * 60 + seconds
        duration_str = f"{hours:02d}:{minutes:02d}:{seconds:02d}" if hours > 0 else f"{minutes:02d}:{seconds:02d}"
        return duration_str, total_seconds

    async def exists(self, link: str, videoid: Union[bool, str] = None):
        if videoid: link = self.base + link
        return bool(re.search(self.regex, link))

    async def url(self, message_1: Message) -> Union[str, None]:
        messages = [message_1]
        if message_1.reply_to_message: messages.append(message_1.reply_to_message)
        for message in messages:
            if message.entities:
                for entity in message.entities:
                    if entity.type == MessageEntityType.URL:
                        text = message.text or message.caption
                        return text[entity.offset : entity.offset + entity.length]
            elif message.caption_entities:
                for entity in message.caption_entities:
                    if entity.type == MessageEntityType.TEXT_LINK:
                        return entity.url
        return None

    async def details(self, link: str, videoid: Union[bool, str] = None):
        if videoid:
            vidid = link
        else:
            match = re.search(r"(?:v=|\/)([0-9A-Za-z_-]{11})", link)
            vidid = match.group(1) if match else None

        if not vidid:
            search_response = await self.call_api("search", "list", q=link, part="id", maxResults=1, type="video")
            if not search_response or not search_response.get("items"):
                return None
            vidid = search_response["items"][0]["id"]["videoId"]

        video_response = await self.call_api("videos", "list", part="snippet,contentDetails", id=vidid)
        if not video_response or not video_response.get("items"):
            return None

        video_data = video_response["items"][0]
        title = video_data["snippet"]["title"]
        thumbnail = video_data["snippet"]["thumbnails"]["high"]["url"]
        duration_iso = video_data["contentDetails"]["duration"]
        duration_min, duration_sec = self.parse_duration(duration_iso)
        return title, duration_min, duration_sec, thumbnail, vidid

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

    async def video(self, link: str, videoid: Union[bool, str] = None):
        if videoid: link = self.base + link
        opts = ["yt-dlp", "-g", "-f", "best[height<=?720][width<=?1280]", f"{link}"]
        if cookies_file: opts.extend(["--cookies", cookies_file])
        proc = await asyncio.create_subprocess_exec(*opts, stdout=asyncio.subprocess.PIPE, stderr=asyncio.subprocess.PIPE)
        stdout, stderr = await proc.communicate()
        return (1, stdout.decode().split("\n")[0]) if stdout else (0, stderr.decode())

    async def playlist(self, link, limit, user_id, videoid: Union[bool, str] = None):
        if videoid: link = self.listbase + link
        cookie_cmd = f"--cookies {cookies_file}" if cookies_file else ""
        playlist = await shell_cmd(f"yt-dlp {cookie_cmd} -i --get-id --flat-playlist --playlist-end {limit} --skip-download {link}")
        try:
            result = [k for k in playlist.split("\n") if k != ""]
        except:
            result = []
        return result

    async def slider(self, link: str, query_type: int, videoid: Union[bool, str] = None):
        search_response = await self.call_api("search", "list", q=link, part="snippet", maxResults=10, type="video")
        if not search_response or not search_response.get("items"): return None
        result = search_response["items"][query_type]
        vidid = result["id"]["videoId"]
        title = result["snippet"]["title"]
        thumbnail = result["snippet"]["thumbnails"]["high"]["url"]
        video_res = await self.call_api("videos", "list", part="contentDetails", id=vidid)
        if not video_res or not video_res.get("items"): return title, "00:00", thumbnail, vidid
        duration_iso = video_res["items"][0]["contentDetails"]["duration"]
        duration_min, _ = self.parse_duration(duration_iso)
        return title, duration_min, thumbnail, vidid

    async def download(self, link: str, mystic, video=None, videoid=None, songaudio=None, songvideo=None, format_id=None, title=None) -> str:
        if videoid: link = self.base + link
        loop = asyncio.get_running_loop()
        common_opts = {"geo_bypass": True, "nocheckcertificate": True, "quiet": True, "no_warnings": True}
        if cookies_file: common_opts["cookiefile"] = cookies_file

        def dl_func():
            if songvideo:
                ydl_opts = {**common_opts, "format": f"{format_id}+140", "outtmpl": f"downloads/{title}", "merge_output_format": "mp4"}
            elif songaudio:
                ydl_opts = {**common_opts, "format": format_id, "outtmpl": f"downloads/{title}.%(ext)s", "postprocessors": [{"key": "FFmpegExtractAudio", "preferredcodec": "mp3", "preferredquality": "192"}]}
            elif video:
                ydl_opts = {**common_opts, "format": "(bestvideo[height<=?720][width<=?1280][ext=mp4])+(bestaudio[ext=m4a])", "outtmpl": "downloads/%(id)s.%(ext)s"}
            else:
                ydl_opts = {**common_opts, "format": "bestaudio/best", "outtmpl": "downloads/%(id)s.%(ext)s"}
            
            with yt_dlp.YoutubeDL(ydl_opts) as ydl:
                info = ydl.extract_info(link, download=True)
                return ydl.prepare_filename(info)

        downloaded_file = await loop.run_in_executor(None, dl_func)
        return downloaded_file, True
