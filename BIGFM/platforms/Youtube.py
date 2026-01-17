import asyncio
import re
import requests
from typing import Union
from pyrogram.enums import MessageEntityType
from pyrogram.types import Message

# Invidious Instance (Aap badal sakte hain)
INVIDIOUS_INSTANCE = "https://iv.melmac.space" 

class YouTubeAPI:
    def __init__(self):
        self.base = "https://www.youtube.com/watch?v="
        self.regex = r"(?:youtube\.com|youtu\.be)"

    def parse_duration(self, seconds):
        """Seconds ko mm:ss format mein badalne ke liye"""
        minutes, seconds = divmod(seconds, 60)
        hours, minutes = divmod(minutes, 60)
        if hours > 0:
            return f"{hours:02d}:{minutes:02d}:{seconds:02d}"
        return f"{minutes:02d}:{seconds:02d}"

    async def details(self, link: str, videoid: Union[bool, str] = None):
        if videoid: 
            vidid = link
        else:
            match = re.search(r"(?:v=|\/)([0-9A-Za-z_-]{11})", link)
            vidid = match.group(1) if match else None
        
        if not vidid:
            # Agar link nahi hai to Search karein (Invidious API Search)
            try:
                search_url = f"{INVIDIOUS_INSTANCE}/api/v1/search?q={link}&type=video"
                res = requests.get(search_url).json()
                if not res: return None
                vidid = res[0]["videoId"]
            except: return None

        # Invidious API se video ki details nikalna
        try:
            api_url = f"{INVIDIOUS_INSTANCE}/api/v1/videos/{vidid}"
            item = requests.get(api_url).json()
            
            title = item["title"]
            duration_seconds = item["lengthSeconds"]
            duration_str = self.parse_duration(duration_seconds)
            thumbnail = item["videoThumbnails"][0]["url"] # High quality thumb
            
            return title, duration_str, duration_seconds, thumbnail, vidid
        except Exception as e:
            print(f"Error: {e}")
            return None

    async def video(self, link: str, videoid: Union[bool, str] = None):
        """Streaming link nikalne ke liye (Sabse important)"""
        if videoid: vidid = link
        else:
            match = re.search(r"(?:v=|\/)([0-9A-Za-z_-]{11})", link)
            vidid = match.group(1) if match else None

        try:
            api_url = f"{INVIDIOUS_INSTANCE}/api/v1/videos/{vidid}"
            res = requests.get(api_url).json()
            
            # adaptiveFormats mein se audio ya video stream nikalna
            for fmt in res["adaptiveFormats"]:
                # Hum audio stream dhund rahe hain streaming ke liye
                if "audio/" in fmt["type"]:
                    return (1, fmt["url"])
            return (0, "")
        except:
            return (0, "")

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

    # Baaki functions (url, exists) aapke purane wale hi chalengep
