import asyncio
import os
from datetime import datetime, timedelta
from typing import Union

from pyrogram import Client
from pyrogram.types import InlineKeyboardMarkup
from pytgcalls import PyTgCalls

# --- SAFE DYNAMIC IMPORTS (No more ImportErrors) ---
import pytgcalls.types as pytg_types
import pytgcalls.exceptions as pytg_ex

# AudioPiped ko dhundne ki koshish
AudioPiped = getattr(pytg_types, "AudioPiped", None)
AudioVideoPiped = getattr(pytg_types, "AudioVideoPiped", None)
HighQualityAudio = getattr(pytg_types, "HighQualityAudio", None)
MediumQualityVideo = getattr(pytg_types, "MediumQualityVideo", None)
Update = getattr(pytg_types, "Update", None)

# Agar upar wala fail ho jaye (v1.x compatibility)
if not AudioPiped:
    from pytgcalls.types.input_stream import AudioPiped, AudioVideoPiped
    from pytgcalls.types.input_stream.quality import HighQualityAudio, MediumQualityVideo

# StreamEnd handling
try:
    from pytgcalls.types.stream import StreamAudioEnded
except ImportError:
    StreamAudioEnded = Exception

# Exceptions handling
AlreadyJoinedError = getattr(pytg_ex, "AlreadyJoined", getattr(pytg_ex, "AlreadyJoinedError", Exception))
NoActiveGroupCall = getattr(pytg_ex, "NoActiveGroupCall", Exception)
TelegramServerError = getattr(pytg_ex, "TelegramServerError", Exception)
# --------------------------------------------------

import config
from BIGFM import LOGGER, YouTube, app
from BIGFM.misc import db
from BIGFM.utils.database import (
    add_active_chat,
    add_active_video_chat,
    get_lang,
    get_loop,
    group_assistant,
    is_autoend,
    music_on,
    remove_active_chat,
    remove_active_video_chat,
    set_loop,
)
from BIGFM.utils.exceptions import AssistantErr
from BIGFM.utils.formatters import check_duration, seconds_to_min, speed_converter
from BIGFM.utils.inline.play import stream_markup
from BIGFM.utils.stream.autoclear import auto_clean
from BIGFM.utils.thumbnails import gen_thumb
from strings import get_string

autoend = {}
counter = {}

async def _clear_(chat_id):
    db[chat_id] = []
    await remove_active_video_chat(chat_id)
    await remove_active_chat(chat_id)

class Call(PyTgCalls):
    def __init__(self):
        self.userbot1 = Client(name="AviaxAss1", api_id=config.API_ID, api_hash=config.API_HASH, session_string=str(config.STRING1))
        self.one = PyTgCalls(self.userbot1)
        
        self.userbot2 = Client(name="AviaxAss2", api_id=config.API_ID, api_hash=config.API_HASH, session_string=str(config.STRING2))
        self.two = PyTgCalls(self.userbot2)
        
        self.userbot3 = Client(name="AviaxAss3", api_id=config.API_ID, api_hash=config.API_HASH, session_string=str(config.STRING3))
        self.three = PyTgCalls(self.userbot3)
        
        self.userbot4 = Client(name="AviaxAss4", api_id=config.API_ID, api_hash=config.API_HASH, session_string=str(config.STRING4))
        self.four = PyTgCalls(self.userbot4)
        
        self.userbot5 = Client(name="AviaxAss5", api_id=config.API_ID, api_hash=config.API_HASH, session_string=str(config.STRING5))
        self.five = PyTgCalls(self.userbot5)

    async def pause_stream(self, chat_id: int):
        assistant = await group_assistant(self, chat_id)
        await assistant.pause_stream(chat_id)

    async def resume_stream(self, chat_id: int):
        assistant = await group_assistant(self, chat_id)
        await assistant.resume_stream(chat_id)

    async def stop_stream(self, chat_id: int):
        assistant = await group_assistant(self, chat_id)
        try:
            await _clear_(chat_id)
            await assistant.leave_group_call(chat_id)
        except:
            pass

    async def stop_stream_force(self, chat_id: int):
        for ass in [self.one, self.two, self.three, self.four, self.five]:
            try: await ass.leave_group_call(chat_id)
            except: pass
        await _clear_(chat_id)

    async def speedup_stream(self, chat_id: int, file_path, speed, playing):
        assistant = await group_assistant(self, chat_id)
        dur = await asyncio.get_event_loop().run_in_executor(None, check_duration, file_path)
        played, con_seconds = speed_converter(playing[0]["played"], speed)
        duration = seconds_to_min(int(dur))
        
        if playing[0]["streamtype"] == "video":
            stream = AudioVideoPiped(file_path, HighQualityAudio(), MediumQualityVideo(), additional_ffmpeg_parameters=f"-ss {played} -to {duration}")
        else:
            stream = AudioPiped(file_path, HighQualityAudio(), additional_ffmpeg_parameters=f"-ss {played} -to {duration}")
        await assistant.change_stream(chat_id, stream)

    async def stream_call(self, link):
        assistant = await group_assistant(self, config.LOG_GROUP_ID)
        await assistant.join_group_call(config.LOG_GROUP_ID, AudioVideoPiped(link))
        await asyncio.sleep(0.2)
        await assistant.leave_group_call(config.LOG_GROUP_ID)

    async def join_call(self, chat_id: int, original_chat_id: int, link, video: Union[bool, str] = None, image: Union[bool, str] = None):
        assistant = await group_assistant(self, chat_id)
        language = await get_lang(chat_id)
        _ = get_string(language)
        stream = AudioVideoPiped(link, HighQualityAudio(), MediumQualityVideo()) if video else AudioPiped(link, HighQualityAudio())
        try:
            await assistant.join_group_call(chat_id, stream)
        except NoActiveGroupCall:
            raise AssistantErr(_["call_8"])
        except AlreadyJoinedError:
            raise AssistantErr(_["call_9"])
        except TelegramServerError:
            raise AssistantErr(_["call_10"])
        await add_active_chat(chat_id)
        await music_on(chat_id)

    async def change_stream(self, client, chat_id):
        check = db.get(chat_id)
        if not check: return
        try:
            popped = check.pop(0)
            await auto_clean(popped)
            if not check:
                await _clear_(chat_id)
                return await client.leave_group_call(chat_id)
            
            queued = check[0]["file"]
            video = True if str(check[0]["streamtype"]) == "video" else False
            stream = AudioVideoPiped(queued, HighQualityAudio(), MediumQualityVideo()) if video else AudioPiped(queued, HighQualityAudio())
            await client.change_stream(chat_id, stream)
        except:
            pass

    async def ping(self):
        pings = []
        for obj in [self.one, self.two, self.three, self.four, self.five]:
            try: pings.append(await obj.ping)
            except: pass
        return str(round(sum(pings) / len(pings), 3)) if pings else "0"

    async def start(self):
        for ass in [self.one, self.two, self.three, self.four, self.five]:
            await ass.start()

    async def decorators(self):
        @self.one.on_stream_end()
        @self.two.on_stream_end()
        @self.three.on_stream_end()
        @self.four.on_stream_end()
        @self.five.on_stream_end()
        async def handler(client, update: Update):
            if isinstance(update, StreamAudioEnded):
                await self.change_stream(client, update.chat_id)

Aviax = Call()
