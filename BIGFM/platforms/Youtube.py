import asyncio
import os
import re
import glob
import random
import yt_dlp
import isodate
from typing import Union
from pyrogram.types import Message
from pyrogram.enums import MessageEntityType
from googleapiclient.discovery import build

# ================= CONFIGURATION =================
# अपनी Google Cloud Console वाली API Key यहाँ डालें
YOUTUBE_API_KEY = "AIzaSyCFv5iwf9_CZKYcifMFK43zMZ78NH5GwE8"
# =================================================

# YouTube API Client Setup
youtube_client = build("youtube", "v3", developerKey=YOUTUBE_API_KEY)

def get_random_cookie():
    """Cookies फोल्डर से रैंडमली एक .txt फाइल चुनता है"""
    folder_path = os.path.join(os.getcwd(), "cookies")
    if not os.path.exists(folder_path):
        os.makedirs(folder_path)
    txt_files = glob.glob(os.path.join(folder_path, '*.txt'))
    if not txt_files:
        return None
    return random.choice(txt_files)

def parse_duration(duration_iso):
    """ISO 8601 duration (PT1M2S) को mm:ss और seconds में बदलता है"""
    try:
        seconds = int(isodate.parse_duration(duration_iso).total_seconds())
        minutes, sec = divmod(seconds, 60)
        hours, minutes = divmod(minutes, 60)
        if hours > 0:
            return f"{hours:02d}:{minutes:02d}:{sec:02d}", seconds
        return f"{minutes:02d}:{sec:02d}", seconds
    except Exception:
        return "00:00", 0

async def shell_cmd(cmd):
    proc = await asyncio.create_subprocess_shell(
        cmd,
        stdout=asyncio.subprocess.PIPE,
        stderr=asyncio.subprocess.PIPE,
    )
    out, errorz = await proc.communicate()
    return out.decode("utf-8") if out else errorz.decode("utf-8")

class YouTubeAPI:
    def __init__(self):
        self.base = "https://www.youtube.com/watch?v="
        self.regex = r"(?:youtube\.com|youtu\.be)"
        self.listbase = "https://youtube.com/playlist?list="

    async def exists(self, link: str, videoid: Union[bool, str] = None):
        if videoid:
            link = self.base + link
        return bool(re.search(self.regex, link))

    async def url(self, message: Message) -> Union[str, None]:
        messages = [message]
        if message.reply_to_message:
            messages.append(message.reply_to_message)
        
        for msg in messages:
            if msg.entities:
                for entity in msg.entities:
                    if entity.type == MessageEntityType.URL:
                        text = msg.text or msg.caption
                        return text[entity.offset : entity.offset + entity.length]
            if msg.caption_entities:
                for entity in msg.caption_entities:
                    if entity.type == MessageEntityType.TEXT_LINK:
                        return entity.url
        return None

    async def get_video_id(self, link: str):
        regex = r"(?:v=|\/)([0-9A-Za-z_-]{11}).*"
        match = re.search(regex, link)
        return match.group(1) if match else None

    async def details(self, link: str, videoid: Union[bool, str] = None):
        loop = asyncio.get_event_loop()
        v_id = link if videoid else await self.get_video_id(link)
        
        # अगर ID नहीं मिली तो सर्च करें
        if not v_id:
            search_request = await loop.run_in_executor(None, lambda: youtube_client.search().list(
                q=link, part="id", maxResults=1, type="video"
            ).execute())
            if not search_request.get("items"):
                return None, None, None, None, None
            v_id = search_request["items"][0]["id"]["videoId"]

        # वीडियो डेटा निकालें
        video_request = await loop.run_in_executor(None, lambda: youtube_client.videos().list(
            id=v_id, part="snippet,contentDetails"
        ).execute())

        if not video_request.get("items"):
            return None, None, None, None, None

        item = video_request["items"][0]
        title = item["snippet"]["title"]
        duration_min, duration_sec = parse_duration(item["contentDetails"]["duration"])
        thumbnail = item["snippet"]["thumbnails"]["high"]["url"]
        
        return title, duration_min, duration_sec, thumbnail, v_id

    async def title(self, link: str, videoid: Union[bool, str] = None):
        res = await self.details(link, videoid)
        return res[0]

    async def track(self, link: str, videoid: Union[bool, str] = None):
        title, duration_min, duration_sec, thumbnail, v_id = await self.details(link, videoid)
        track_details = {
            "title": title,
            "link": self.base + v_id,
            "vidid": v_id,
            "duration_min": duration_min,
            "thumb": thumbnail,
        }
        return track_details, v_id

    async def playlist(self, link, limit, user_id, videoid: Union[bool, str] = None):
        if videoid:
            link = self.listbase + link
        if "&" in link:
            link = link.split("&")[0]
        playlist = await shell_cmd(
            f"yt-dlp -i --get-id --flat-playlist --playlist-end {limit} --skip-download {link}"
        )
        return [x for x in playlist.split("\n") if x]

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

        # फाइल नेम से खराब कैरेक्टर हटाना
        clean_title = re.sub(r'[^\w\s-]', '', title) if title else "track"

        def download_logic():
            if not os.path.exists("downloads"):
                os.makedirs("downloads")
            
            cookie_file = get_random_cookie()
            save_path = f"downloads/{clean_title}"
            
            ydl_opts = {
                "quiet": True,
                "no_warnings": True,
                "geo_bypass": True,
                "nocheckcertificate": True,
                "cookiefile": cookie_file,
            }

            if songvideo:
                ydl_opts.update({
                    "format": f"{format_id}+140/bestvideo+bestaudio",
                    "outtmpl": f"{save_path}.mp4",
                    "merge_output_format": "mp4"
                })
                final_file = f"{save_path}.mp4"
            elif songaudio:
                ydl_opts.update({
                    "format": "bestaudio/best",
                    "outtmpl": save_path,
                    "postprocessors": [{
                        "key": "FFmpegExtractAudio",
                        "preferredcodec": "mp3",
                        "preferredquality": "192",
                    }]
                })
                final_file = f"{save_path}.mp3"
            elif video:
                ydl_opts.update({
                    "format": "bestvideo[height<=720]+bestaudio/best",
                    "outtmpl": f"downloads/%(id)s.%(ext)s"
                })
                # yt-dlp determine name
            else:
                ydl_opts.update({
                    "format": "bestaudio/best",
                    "outtmpl": f"downloads/%(id)s.%(ext)s"
                })

            with yt_dlp.YoutubeDL(ydl_opts) as ydl:
                info = ydl.extract_info(link, download=True)
                if not songvideo and not songaudio:
                    final_file = ydl.prepare_filename(info)
                
                return final_file

        try:
            file_path = await loop.run_in_executor(None, download_logic)
            return file_path, None
        except Exception as e:
            print(f"Download error: {e}")
            return None, None
