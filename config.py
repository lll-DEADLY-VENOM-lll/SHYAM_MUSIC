# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
#     ⚙️ CONFIGURATION FILE | SHYAM VIBE MUSIC BOT
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

import os
import re
from dotenv import load_dotenv
from pyrogram import filters

load_dotenv()

# 🛠️ HELPER FUNCTION FOR SAFE INTEGER CONVERSION
# Yeh function bot ko crash hone se bachayega agar ID khali reh jaye toh.
def get_int_env(key: str, default: int) -> int:
    value = os.getenv(key)
    if value and value.strip():
        try:
            return int(value)
        except ValueError:
            return default
    return default

# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
# 📲 Telegram & API Credentials
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

# API_ID fix: Agar khali hua toh bot crash nahi hoga, default 0 lega.
API_ID = get_int_env("API_ID", 0) 
API_HASH = os.getenv("API_HASH", "")
BOT_TOKEN = os.getenv("BOT_TOKEN", "")

# OWNER_ID fix: Default value 8520496440 set hai.
OWNER_ID = get_int_env("OWNER_ID", 8520496440)
OWNER_USERNAME = os.getenv("OWNER_USERNAME", "KIRU_OP")

# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
# 🛠️ Database & Deployment Configs
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

MONGO_DB_URI = os.getenv("MONGO_DB_URI", "")
LOG_GROUP_ID = get_int_env("LOG_GROUP_ID", -1003034048678)
HEROKU_APP_NAME = os.getenv("HEROKU_APP_NAME", "")
HEROKU_API_KEY = os.getenv("HEROKU_API_KEY", "") 

# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
# 🔄 Git & Update Settings
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

UPSTREAM_REPO = os.getenv("UPSTREAM_REPO", "https://github.com/TANYA-SINGH-VNS-UP/SHYANVIBE")
UPSTREAM_BRANCH = os.getenv("UPSTREAM_BRANCH", "main")
GIT_TOKEN = os.getenv("GIT_TOKEN", None)

# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
# 🔗 Support Links
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

SUPPORT_CHANNEL = os.getenv("SUPPORT_CHANNEL", "https://t.me/HEROKU_CLUB")
SUPPORT_GROUP = os.getenv("SUPPORT_GROUP", "https://t.me/NOBITA_SUPPORT")
PRIVACY_LINK = os.getenv("PRIVACY_LINK", "https://graph.org/Privacy-Policy-05-01-30")

# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
# ⏱️ Duration & Playlist Settings
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

DURATION_LIMIT_MIN = get_int_env("DURATION_LIMIT", 300)
PLAYLIST_FETCH_LIMIT = get_int_env("PLAYLIST_FETCH_LIMIT", 25)

# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
# 📦 File Size Limits (in bytes)
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

TG_AUDIO_FILESIZE_LIMIT = get_int_env("TG_AUDIO_FILESIZE_LIMIT", 104857600)
TG_VIDEO_FILESIZE_LIMIT = get_int_env("TG_VIDEO_FILESIZE_LIMIT", 2145386496)

# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
# 🎧 Spotify Developer Credentials
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

SPOTIFY_CLIENT_ID = os.getenv("SPOTIFY_CLIENT_ID", None)
SPOTIFY_CLIENT_SECRET = os.getenv("SPOTIFY_CLIENT_SECRET", None)

# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
# 🧵 Session Strings (Pyrogram V2)
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

STRING1 = os.getenv("STRING_SESSION", "")
STRING2 = os.getenv("STRING_SESSION2", None)
STRING3 = os.getenv("STRING_SESSION3", None)
STRING4 = os.getenv("STRING_SESSION4", None)
STRING5 = os.getenv("STRING_SESSION5", None)

# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
# ⚙️ Runtime Configurations
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

AUTO_LEAVING_ASSISTANT = os.getenv("AUTO_LEAVING_ASSISTANT", "False").lower() == "true"

# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
# 🖼️ Image URLs
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

START_IMG_URL = os.getenv("START_IMG_URL", "https://graph.org/file/cdac0910ad60867e08cd2-eec1ead13b60905f29.jpg")
PING_IMG_URL = os.getenv("PING_IMG_URL", "https://graph.org/file/cdac0910ad60867e08cd2-eec1ead13b60905f29.jpg")
PLAYLIST_IMG_URL = "https://graph.org/file/cdac0910ad60867e08cd2-eec1ead13b60905f29.jpg"
STATS_IMG_URL = "https://graph.org/file/cdac0910ad60867e08cd2-eec1ead13b60905f29.jpg"
TELEGRAM_AUDIO_URL = "https://graph.org/file/cdac0910ad60867e08cd2-eec1ead13b60905f29.jpg"
TELEGRAM_VIDEO_URL = "https://graph.org/file/cdac0910ad60867e08cd2-eec1ead13b60905f29.jpg"
STREAM_IMG_URL = "https://graph.org/file/cdac0910ad60867e08cd2-eec1ead13b60905f29.jpg"
SOUNCLOUD_IMG_URL = "https://graph.org/file/cdac0910ad60867e08cd2-eec1ead13b60905f29.jpg"
YOUTUBE_IMG_URL = "https://graph.org/file/cdac0910ad60867e08cd2-eec1ead13b60905f29.jpg"
SPOTIFY_ARTIST_IMG_URL = "https://graph.org/file/cdac0910ad60867e08cd2-eec1ead13b60905f29.jpg"
SPOTIFY_ALBUM_IMG_URL = "https://graph.org/file/cdac0910ad60867e08cd2-eec1ead13b60905f29.jpg"
SPOTIFY_PLAYLIST_IMG_URL = "https://graph.org/file/cdac0910ad60867e08cd2-eec1ead13b60905f29.jpg"

# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
# 🔐 User & Bot State Stores
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

BANNED_USERS = filters.user()
adminlist = {}
lyrical = {}
votemode = {}
autoclean = []
confirmer = {}

# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
# ⏳ Time Conversion Utility
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

def time_to_seconds(time):
    stringt = str(time)
    try:
        return sum(int(x) * 60**i for i, x in enumerate(reversed(stringt.split(":"))))
    except (ValueError, TypeError):
        return 0

# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
# ❌ Validate Support Links
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

if SUPPORT_CHANNEL:
    if not re.match(r"(?:http|https)://", SUPPORT_CHANNEL):
        raise SystemExit("[ERROR] - SUPPORT_CHANNEL URL is invalid.")

if SUPPORT_GROUP:
    if not re.match(r"(?:http|https)://", SUPPORT_GROUP):
        raise SystemExit("[ERROR] - SUPPORT_GROUP URL is invalid.")

# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
#     ✅ CONFIG LOADED SUCCESSFULLY | Fixed By KIRU
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
