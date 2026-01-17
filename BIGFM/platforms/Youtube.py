import asyncio, os, re, glob, random
import yt_dlp
import isodate 
from typing import Union
from pyrogram.types import Message
from pyrogram.enums import MessageEntityType
from googleapiclient.discovery import build

# अपनी API Key यहाँ डालें
YOUTUBE_API_KEY = "YOUR_GOOGLE_API_KEY_HERE"

youtube_client = build("youtube", "v3", developerKey=YOUTUBE_API_KEY)

# कुकीज़ फाइल चुनने के लिए फंक्शन
def get_random_cookie():
    folder_path = f"{os.getcwd()}/cookies"
    if not os.path.exists(folder_path):
        os.makedirs(folder_path)
    txt_files = glob.glob(os.path.join(folder_path, '*.txt'))
    if not txt_files:
        return None
    return random.choice(txt_files)

def parse_duration(duration_iso):
    try:
        seconds = int(isodate.parse_duration(duration_iso).total_seconds())
        minutes, sec = divmod(seconds, 60)
        hours, minutes = divmod(minutes, 60)
        if hours > 0:
            return f"{hours:02d}:{minutes:02d}:{sec:02d}", seconds
        return f"{minutes:02d}:{sec:02d}", seconds
    except:
        return "00:00", 0

class YouTubeAPI:
    def __init__(self):
        self.base = "https://www.youtube.com/watch?v="
        self.regex = r"(?:youtube\.com|youtu\.be)"
        self.listbase = "https://youtube.com/playlist?list="

    async def exists(self, link: str, videoid: Union[bool, str] = None):
        if videoid:
            link = self.base + link
        if re.search(self.regex, link):
            return True
        return False

    async def url(self, message_1: Message) -> Union[str, None]:
        messages = [message_1]
        if message_1.reply_to_message:
            messages.append(message_1.reply_to_message)
        text = ""
        offset = None
        length = None
        for message in messages:
            if offset:
                break
            if message.entities:
                for entity in message.entities:
                    if entity.type == MessageEntityType.URL:
                        text = message.text or message.caption
                        offset, length = entity.offset, entity.length
                        break
            elif message.caption_entities:
                for entity in message.caption_entities:
                    if entity.type == MessageEntityType.TEXT_LINK:
                        return entity.url
        if offset is None:
            return None
        return text[offset : offset + length]

    async def get_video_id(self, link: str):
        regex = r"(?:v=|\/)([0-9A-Za-z_-]{11}).*"
        match = re.search(regex, link)
        return match.group(1) if match else None

    async def details(self, link: str, videoid: Union[bool, str] = None):
        loop = asyncio.get_event_loop()
        v_id = link if videoid else await self.get_video_id(link)
        
        if not v_id:
            search_request = await loop.run_in_executor(None, lambda: youtube_client.search().list(
                q=link, part="id", maxResults=1, type="video"
            ).execute())
            if not search_request.get("items"):
                return None, None, None, None, None
            v_id = search_request["items"][0]["id"]["videoId"]

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

        def download_logic():
            cookie_file = get_random_cookie()
            ydl_opts = {
                "quiet": True,
                "no_warnings": True,
                "geo_bypass": True,
                "nocheckcertificate": True,
                "cookiefile": cookie_file, # यहाँ कुकी फ़ाइल का इस्तेमाल होगा
            }

            if songvideo:
                ydl_opts.update({"format": f"{format_id}+140", "outtmpl": f"downloads/{title}.mp4", "merge_output_format": "mp4"})
            elif songaudio:
                ydl_opts.update({"format": format_id, "outtmpl": f"downloads/{title}.%(ext)s", 
                                "postprocessors": [{"key": "FFmpegExtractAudio", "preferredcodec": "mp3", "preferredquality": "192"}]})
            elif video:
                ydl_opts.update({"format": "bestvideo[height<=720]+bestaudio/best", "outtmpl": "downloads/%(id)s.%(ext)s"})
            else:
                ydl_opts.update({"format": "bestaudio/best", "outtmpl": "downloads/%(id)s.%(ext)s"})

            with yt_dlp.YoutubeDL(ydl_opts) as ydl:
                info = ydl.extract_info(link, download=True)
                return ydl.prepare_filename(info)

        file_path = await loop.run_in_executor(None, download_logic)
        return file_path, None
