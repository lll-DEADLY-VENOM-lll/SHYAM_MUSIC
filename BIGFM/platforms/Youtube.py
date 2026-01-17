import asyncio
import os
import re
from typing import Union, Optional

import yt_dlp
from pyrogram.enums import MessageEntityType
from pyrogram.types import Message
from googleapiclient.discovery import build
from googleapiclient.errors import HttpError

# 🔹 Direct API keys (optional)
YOUTUBE_API_KEYS = [ "AIzaSyBlbkp4_XbjOZAMG6mr_QMmurBW9tcpu0s" ]   # ["API_KEY_1", "API_KEY_2"]


class YouTubeAPI:
    current_key_index = 0
    youtube_client = None

    def __init__(self):
        self.base = "https://www.youtube.com/watch?v="
        self.regex = re.compile(r"(youtube\.com|youtu\.be)")
        if YOUTUBE_API_KEYS and YouTubeAPI.youtube_client is None:
            self._build_client()

    # ---------- URL PARSER ----------
    async def url(self, message: Message) -> Optional[str]:
        for msg in filter(None, [message, message.reply_to_message]):
            text = msg.text or msg.caption
            entities = msg.entities or msg.caption_entities or []
            for e in entities:
                if e.type == MessageEntityType.URL:
                    return text[e.offset:e.offset + e.length]
                if e.type == MessageEntityType.TEXT_LINK:
                    return e.url
        return None

    # ---------- YOUTUBE API ----------
    def _build_client(self):
        try:
            YouTubeAPI.youtube_client = build(
                "youtube",
                "v3",
                developerKey=YOUTUBE_API_KEYS[self.current_key_index],
                static_discovery=False
            )
        except Exception:
            YouTubeAPI.youtube_client = None

    def _rotate_key(self):
        if len(YOUTUBE_API_KEYS) > 1:
            self.current_key_index = (self.current_key_index + 1) % len(YOUTUBE_API_KEYS)
            self._build_client()

    # ---------- DURATION ----------
    def parse_duration(self, duration: str):
        if not duration:
            return "00:00", 0

        match = re.search(r'PT(?:(\d+)H)?(?:(\d+)M)?(?:(\d+)S)?', duration)
        if not match:
            return "00:00", 0

        h = int(match.group(1) or 0)
        m = int(match.group(2) or 0)
        s = int(match.group(3) or 0)

        total = h * 3600 + m * 60 + s
        return (f"{h:02d}:{m:02d}:{s:02d}" if h else f"{m:02d}:{s:02d}"), total

    # ---------- DETAILS ----------
    async def details(self, link: str, videoid=False):
        vidid = link if videoid else self._extract_id(link)

        # ---- GOOGLE API (if key exists) ----
        if YOUTUBE_API_KEYS and YouTubeAPI.youtube_client:
            for _ in range(len(YOUTUBE_API_KEYS)):
                try:
                    res = await asyncio.to_thread(
                        YouTubeAPI.youtube_client.videos().list(
                            part="snippet,contentDetails",
                            id=vidid
                        ).execute
                    )
                    item = res["items"][0]
                    title = item["snippet"]["title"]
                    thumb = item["snippet"]["thumbnails"]["high"]["url"]
                    d_min, d_sec = self.parse_duration(item["contentDetails"]["duration"])
                    return title, d_min, d_sec, thumb, vidid
                except HttpError as e:
                    if e.resp.status in (403, 429):
                        self._rotate_key()
                        continue
                except Exception:
                    break

        # ---- YT-DLP FALLBACK ----
        try:
            ydl_opts = {
                "quiet": True,
                "no_warnings": True,
                "skip_download": True,
                "geo_bypass": True,
                "format": "bestaudio/best"
            }

            query = f"ytsearch1:{link}" if not vidid else f"{self.base}{vidid}"
            loop = asyncio.get_running_loop()

            with yt_dlp.YoutubeDL(ydl_opts) as ydl:
                info = await loop.run_in_executor(
                    None, lambda: ydl.extract_info(query, False)
                )
                data = info["entries"][0] if "entries" in info else info

                return (
                    data.get("title", "Unknown"),
                    data.get("duration_string", "00:00"),
                    data.get("duration", 0),
                    data.get("thumbnail"),
                    data.get("id"),
                )
        except Exception:
            return None

    # ---------- HELPERS ----------
    def _extract_id(self, url):
        m = re.search(r"(?:v=|/)([0-9A-Za-z_-]{11})", url)
        return m.group(1) if m else None

    async def exists(self, link):
        return bool(self.regex.search(link))

    async def video(self, link):
        cmd = [
            "yt-dlp", "-g",
            "-f", "best[height<=720][ext=mp4]/best",
            "--no-playlist",
            "--geo-bypass",
            link
        ]
        proc = await asyncio.create_subprocess_exec(
            *cmd, stdout=asyncio.subprocess.PIPE
        )
        out, _ = await proc.communicate()
        return out.decode().strip() if out else None

    async def download(self, link, video=False):
        loop = asyncio.get_running_loop()

        def _dl():
            opts = {
                "format": "best[height<=720][ext=mp4]" if video else "bestaudio/best",
                "outtmpl": "downloads/%(id)s.%(ext)s",
                "quiet": True,
            }
            with yt_dlp.YoutubeDL(opts) as ydl:
                info = ydl.extract_info(link, True)
                return f"downloads/{info['id']}.{info['ext']}"

        return await loop.run_in_executor(None, _dl)


