import math
from pyrogram.types import InlineKeyboardButton
from BIGFM.utils.formatters import time_to_seconds

# --- [ 1. PROGRESS BAR (Photo Style) ] ---
def get_progress_bar(played_sec, total_sec):
    try:
        percentage = (played_sec / total_sec) * 100
    except ZeroDivisionError:
        percentage = 0
    
    show = math.floor(percentage / 10) 
    
    if show == 0:
        bar = "♬—————————"
    elif show == 1:
        bar = "—♬————————"
    elif show == 2:
        bar = "——♬———————"
    elif show == 3:
        bar = "———♬——————"
    elif show == 4:
        bar = "————♬—————"
    elif show == 5:
        bar = "—————♬————"
    elif show == 6:
        bar = "——————♬———"
    elif show == 7:
        bar = "———————♬——"
    elif show == 8:
        bar = "————————♬—"
    elif show >= 9:
        bar = "—————————♬"
    else:
        bar = "——————————"
    
    return bar

# --- [ 2. STREAM MARKUP TIMER (With Cancel Button) ] ---
def stream_markup_timer(_, chat_id, played, dur):
    played_sec = time_to_seconds(played)
    duration_sec = time_to_seconds(dur)
    progress_bar = get_progress_bar(played_sec, duration_sec)

    return [
        [
            # Row 1: Time and Progress Bar
            InlineKeyboardButton(
                text=f"{played} |{progress_bar}| {dur}", 
                callback_data="timer_noop"
            )
        ],
        [
            # Row 2: Control Buttons
            InlineKeyboardButton(text="▷", callback_data=f"ADMIN Resume|{chat_id}"),
            InlineKeyboardButton(text="Ⅱ", callback_data=f"ADMIN Pause|{chat_id}"),
            InlineKeyboardButton(text="⏭", callback_data=f"ADMIN Skip|{chat_id}"),
            InlineKeyboardButton(text="↺", callback_data=f"ADMIN Replay|{chat_id}"),
            InlineKeyboardButton(text="▢", callback_data=f"ADMIN Stop|{chat_id}"),
        ],
        [
            # Row 3: Normal Cancel Button
            InlineKeyboardButton(text="Cancel", callback_data=f"ADMIN Stop|{chat_id}")
        ],
    ]

# --- [ 3. SIMPLE MARKUP ] ---
def stream_markup(_, chat_id):
    return [
        [
            InlineKeyboardButton(text="▷", callback_data=f"ADMIN Resume|{chat_id}"),
            InlineKeyboardButton(text="Ⅱ", callback_data=f"ADMIN Pause|{chat_id}"),
            InlineKeyboardButton(text="⏭", callback_data=f"ADMIN Skip|{chat_id}"),
            InlineKeyboardButton(text="↺", callback_data=f"ADMIN Replay|{chat_id}"),
            InlineKeyboardButton(text="▢", callback_data=f"ADMIN Stop|{chat_id}"),
        ],
        [InlineKeyboardButton(text="Cancel", callback_data=f"ADMIN Stop|{chat_id}")],
    ]

# --- [ 4. TRACK MARKUP ] ---
def track_markup(_, videoid, user_id, channel, fplay):
    return [
        [
            InlineKeyboardButton(text="ᴀᴜᴅɪᴏ", callback_data=f"MusicStream {videoid}|{user_id}|a|{channel}|{fplay}"),
            InlineKeyboardButton(text="ᴠɪᴅᴇᴏ", callback_data=f"MusicStream {videoid}|{user_id}|v|{channel}|{fplay}"),
        ],
        [InlineKeyboardButton(text="Cancel", callback_data=f"forceclose {videoid}|{user_id}")],
    ]

# --- [ 5. LIVESTREAM MARKUP ] ---
def livestream_markup(_, videoid, user_id, mode, channel, fplay):
    return [
        [
            InlineKeyboardButton(text="ʟɪᴠᴇ sᴛʀᴇᴀᴍ", callback_data=f"LiveStream {videoid}|{user_id}|{mode}|{channel}|{fplay}"),
        ],
        [InlineKeyboardButton(text="Cancel", callback_data=f"forceclose {videoid}|{user_id}")],
    ]
