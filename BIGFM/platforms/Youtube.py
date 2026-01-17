import asyncio
import re
import requests
from typing import Union
from pyrogram.enums import MessageEntityType
from pyrogram.types import Message

# Invidious Instance
INVIDIOUS_INSTANCE = "https://iv.melmac.space" 

class YouTubeAPI:
    def __init__(self):
        self.base = "https://www.youtube.com/watch?v="
        self.regex = r"(?:youtube\.com|youtu\.be)"
        self.listbase = "https://youtube.com/playlist?list="

    def parse_duration(self, seconds):
        minutes, seconds = divmod(seconds, 60)
        hours, minutes = divmod(minutes, 60)
        if hours > 0:
            return f"{hours:02d}:{minutes:02d}:{seconds:02d}"
        return f"{minutes:02d}:{seconds:02d}"

    # Ye function wapas add kiya hai (Missing Attribute Error fix)
    async def exists(self, link: str, videoid: Union[bool, str] = None):
        if videoid: link = self.base + link
        return bool(re.search(self.regex, link))

    # Ye function wapas add kiya hai (Missing Attribute Error fix)
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
            try:
                # Agar direct link nahi hai to search karein
                search_url = f"{INVIDIOUS_INSTANCE}/api/v1/search?q={link}&type=video"
                res = requests.get(search_url).json()
                if not res: return None
                vidid = res[0]["videoId"]
            except: return None

        try:
            api_url = f"{INVIDIOUS_INSTANCE}/api/v1/videos/{vidid}"
            item = requests.get(api_url).json()
            title = item["title"]
            duration_seconds = item["lengthSeconds"]
            duration_str = self.parse_duration(duration_seconds)
            thumbnail = item["videoThumbnails"][0]["url"]
            return title, duration_str, duration_seconds, thumbnail, vidid
        except:
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
        title, d_min, d_sec, thumb, vidid = res
        return {
            "title": title, 
            "link": self.base + vidid, 
            "vidid": vidid, 
            "duration_min": d_min, 
            "thumb": thumb
        }, vidid

    async def video(self, link: str, videoid: Union[bool, str] = None):
        if videoid: vidid = link
        else:
            match = re.search(r"(?:v=|\/)([0-9A-Za-z_-]{11})", link)
            vidid = match.group(1) if match else None

        try:
            api_url = f"{INVIDIOUS_INSTANCE}/api/v1/videos/{vidid}"
            res = requests.get(api_url).json()
            # Adaptive format se direct stream link nikalna
            for fmt in res["adaptiveFormats"]:
                if "audio/" in fmt["type"]:
                    return (1, fmt["url"])
            return (0, "")
        except:
            return (0, "")

    # Playlist support (yt-dlp use kar raha hai bina download ke)
    async def playlist(self, link, limit, user_id, videoid: Union[bool, str] = None):
        if videoid: link = self.listbase + link
        import subprocess
        cmd = f"yt-dlp -i --get-id --flat-playlist --playlist-end {limit} --skip-download {link}"
        playlist = subprocess.check_output(cmd, shell=True).decode().split("\n")
        return [k for k in playlist if k != ""]
