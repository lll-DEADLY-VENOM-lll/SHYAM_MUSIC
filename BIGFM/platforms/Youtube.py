import asyncio
import os
import re
from typing import Union

import yt_dlp
from pyrogram.enums import MessageEntityType
from pyrogram.types import Message
from googleapiclient.discovery import build 

# --- CONFIGURATION ---
API_KEY = "AIzaSyCfKiSfgok3-MMJsQfIVIuXC7dHB9m1xnc" 

# Global instance of YouTube API
youtube = build("youtube", "v3", developerKey=API_KEY, static_discovery=False)

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

cookies_file = "BIGFM/cookies.txt"
if not os.path.exists(cookies_file):
    cookies_file = None

class YouTubeAPI:
    def __init__(self):
        self.base = "https://www.youtube.com/watch?v="
        self.regex = r"(?:youtube\.com|youtu\.be)"
        self.listbase = "https://youtube.com/playlist?list="

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
        if message_1.reply_to_message:
            messages.append(message_1.reply_to_message)
        for message in messages:
            if message.entities:
                for entity in message.entities:
                    if entity.type == MessageEntityType.URL:
                        text = message.text or message.caption
                        return text[entity.offset : entity.offset + entity.length]
        return None

    async def details(self, link: str, videoid: Union[bool, str] = None):
        if videoid:
            vidid = link
        else:
            match = re.search(r"(?:v=|\/)([0-9A-Za-z_-]{11})", link)
            vidid = match.group(1) if match else None
        if not vidid:
            search_response = await asyncio.to_thread(youtube.search().list(q=link, part="id", maxResults=1, type="video").execute)
            if not search_response.get("items"): return None
            vidid = search_response["items"][0]["id"]["videoId"]
        video_response = await asyncio.to_thread(youtube.videos().list(part="snippet,contentDetails", id=vidid).execute)
        if not video_response.get("items"): return None
        video_data = video_response["items"][0]
        return (video_data["snippet"]["title"], *self.parse_duration(video_data["contentDetails"]["duration"]), 
                video_data["snippet"]["thumbnails"]["high"]["url"], vidid)

    # --- VPLAY OFF LOGIC ---
    async def video(self, link: str, videoid: Union[bool, str] = None):
        """Vplay ko band kar diya gaya hai"""
        return 0, "❌ Video playback is disabled by Owner. Please use /play for audio."

    async def title(self, link: str, videoid: Union[bool, str] = None):
        res = await self.details(link, videoid)
        return res[0] if res else "Unknown"

    async def track(self, link: str, videoid: Union[bool, str] = None):
        res = await self.details(link, videoid)
        if not res: return None, None
        title, d_min, d_sec, thumb, vidid = res
        return {"title": title, "link": self.base + vidid, "vidid": vidid, "duration_min": d_min, "thumb": thumb}, vidid

    async def playlist(self, link, limit, user_id, videoid: Union[bool, str] = None):
        if videoid: link = self.listbase + link
        cookie_cmd = f"--cookies {cookies_file}" if cookies_file else ""
        playlist = await shell_cmd(f"yt-dlp {cookie_cmd} -i --get-id --flat-playlist --playlist-end {limit} --skip-download {link}")
        return [k for k in playlist.split("\n") if k != ""]

    async def download(self, link: str, mystic, video=None, videoid=None, songaudio=None, songvideo=None, format_id=None, title=None) -> str:
        if videoid: link = self.base + link
        loop = asyncio.get_running_loop()
        common_opts = {"geo_bypass": True, "nocheckcertificate": True, "quiet": True, "no_warnings": True}
        if cookies_file: common_opts["cookiefile"] = cookies_file

        # Video requests ko bhi audio mein convert kar dega
        def audio_dl():
            ydl_opts = {**common_opts, "format": "bestaudio/best", "outtmpl": "downloads/%(id)s.%(ext)s"}
            with yt_dlp.YoutubeDL(ydl_opts) as ydl:
                info = ydl.extract_info(link, False)
                path = os.path.join("downloads", f"{info['id']}.{info['ext']}")
                if not os.path.exists(path): ydl.download([link])
                return path

        if songvideo or video:
            return None, "❌ Video downloading is disabled."

        if songaudio:
            fpath = f"downloads/{title}.mp3"
            def sa_dl():
                with yt_dlp.YoutubeDL({**common_opts, "format": format_id, "outtmpl": f"downloads/{title}.%(ext)s", "postprocessors": [{"key": "FFmpegExtractAudio", "preferredcodec": "mp3", "preferredquality": "192"}]}) as ydl:
                    ydl.download([link])
            await loop.run_in_executor(None, sa_dl)
            return fpath

        downloaded_file = await loop.run_in_executor(None, audio_dl)
        return downloaded_file, True
