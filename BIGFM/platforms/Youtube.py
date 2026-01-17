import asyncio
import re
import requests
import random
from typing import Union
from pyrogram.enums import MessageEntityType
from pyrogram.types import Message

# Zyada aur fast instances ki list
INSTANCES = [
    "https://invidious.snopyta.org",
    "https://yewtu.be",
    "https://inv.tux.rs",
    "https://invidious.kavin.rocks",
    "https://vid.privex.io",
    "https://invidious.namazso.eu",
    "https://inv.riverside.rocks",
    "https://invidious.projectsegfau.lt",
    "https://invidious.slipfox.xyz",
    "https://invidious. domain.glass",
    "https://iv.melmac.space"
]

class YouTubeAPI:
    def __init__(self):
        self.base = "https://www.youtube.com/watch?v="
        self.regex = r"(?:youtube\.com|youtu\.be)"
        self.listbase = "https://youtube.com/playlist?list="

    def parse_duration(self, seconds):
        try:
            seconds = int(seconds)
            m, s = divmod(seconds, 60)
            h, m = divmod(m, 60)
            return f"{h:02d}:{m:02d}:{s:02d}" if h > 0 else f"{m:02d}:{s:02d}"
        except: return "00:00"

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
        return None

    async def details(self, link: str, videoid: Union[bool, str] = None):
        if videoid: vidid = link
        else:
            match = re.search(r"(?:v=|\/)([0-9A-Za-z_-]{11})", link)
            vidid = match.group(1) if match else None
        
        # Randomly shuffle instances taaki ek hi par load na pade
        random.shuffle(INSTANCES)
        
        for instance in INSTANCES:
            try:
                # 1. Agar Link nahi hai to Search karein
                if not vidid:
                    search_url = f"{instance}/api/v1/search?q={requests.utils.quote(link)}&type=video"
                    res = requests.get(search_url, timeout=5).json()
                    if res and len(res) > 0:
                        vidid = res[0]["videoId"]
                
                # 2. Video Details nikalna
                if vidid:
                    api_url = f"{instance}/api/v1/videos/{vidid}"
                    item = requests.get(api_url, timeout=5).json()
                    if "title" in item:
                        title = item["title"]
                        duration_seconds = item.get("lengthSeconds", 0)
                        duration_str = self.parse_duration(duration_seconds)
                        thumbnail = item["videoThumbnails"][0]["url"] if item.get("videoThumbnails") else ""
                        return title, duration_str, duration_seconds, thumbnail, vidid
            except:
                continue
        return None

    async def track(self, link: str, videoid: Union[bool, str] = None):
        res = await self.details(link, videoid)
        if not res:
            # Agar sab fail ho jaye, to default error return na karke empty dict dein
            # Taaki "Failed to fetch" ki jagah bot handle kar sake
            v_id = videoid if videoid else "dQw4w9WgXcQ"
            return {
                "title": "N/A (Try again)",
                "link": self.base + v_id,
                "vidid": v_id,
                "duration_min": "00:00",
                "thumb": None
            }, v_id
        
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

        random.shuffle(INSTANCES)
        for instance in INSTANCES:
            try:
                api_url = f"{instance}/api/v1/videos/{vidid}"
                res = requests.get(api_url, timeout=7).json()
                if "adaptiveFormats" in res:
                    for fmt in res["adaptiveFormats"]:
                        if "audio/" in fmt["type"]:
                            return (1, fmt["url"])
            except:
                continue
        return (0, "")

    async def playlist(self, link, limit, user_id, videoid: Union[bool, str] = None):
        # Playlist ke liye yt-dlp hi use karna safe hai metadata nikalne ke liye
        try:
            import subprocess
            if videoid: link = self.listbase + link
            cmd = f"yt-dlp -i --get-id --flat-playlist --playlist-end {limit} --skip-download {link}"
            playlist = subprocess.check_output(cmd, shell=True).decode().split("\n")
            return [k for k in playlist if k != ""]
        except: return []
