from typing import Union
from pyrogram.types import InlineKeyboardButton, InlineKeyboardMarkup
from BIGFM import app

# --- PAGE 1 ---
def help_pannel(_, START: Union[bool, int] = None):
    first = [InlineKeyboardButton(text="◁ ʙᴀᴄᴋ", callback_data=f"close")]
    second = [
        InlineKeyboardButton(
            text="◁ ʙᴀᴄᴋ",
            callback_data=f"settingsback_helper",
        ),
    ]
    mark = second if START else first
    
    upl = InlineKeyboardMarkup(
        [
            [
                InlineKeyboardButton(
                    text="ʙᴜɢ ʀᴇᴘᴏʀᴛ sᴇᴄᴛɪᴏɴ",
                    callback_data="help_callback hb1",
                ),
            ],
            [
                InlineKeyboardButton(text="ᴀᴅᴍɪɴ", callback_data="help_callback hb2"),
                InlineKeyboardButton(text="ᴀᴜᴛʜ", callback_data="help_callback hb3"),
                InlineKeyboardButton(text="ʙʟᴀᴄᴋʟɪsᴛ", callback_data="help_callback hb4"),
            ],
            [
                InlineKeyboardButton(text="ʙʀᴏᴀᴅᴄᴀsᴛ", callback_data="help_callback hb5"),
                InlineKeyboardButton(text="ᴘɪɴɢ", callback_data="help_callback hb6"),
                InlineKeyboardButton(text="ᴘʟᴀʏ", callback_data="help_callback hb7"),
            ],
            [
                InlineKeyboardButton(text="sᴜᴅᴏ", callback_data="help_callback hb8"),
                InlineKeyboardButton(text="ᴠɪᴅᴇᴏᴄʜᴀᴛ", callback_data="help_callback hb9"),
                InlineKeyboardButton(text="sᴛᴀʀᴛ", callback_data="help_callback hb10"),
            ],
            [
                InlineKeyboardButton(text="◁ ʙᴀᴄᴋ", callback_data="close"),
                InlineKeyboardButton(text="ᴀᴅᴅ ᴍᴇ", url=f"https://t.me/{app.username}?startgroup=true"),
                InlineKeyboardButton(text="ɴᴇxᴛ ▷", callback_data="help_callback hb_page2"), # Page 2 par jaane ke liye
            ],
            mark,
        ]
    )
    return upl

# --- PAGE 2 (Ye wala missing tha) ---
def help_pannel_2(_, START: Union[bool, int] = None):
    upl = InlineKeyboardMarkup(
        [
            [
                InlineKeyboardButton(text="ʟʏʀɪᴄs", callback_data="help_callback hb11"),
                InlineKeyboardButton(text="ᴘʟᴀʏʟɪsᴛ", callback_data="help_callback hb12"),
                InlineKeyboardButton(text="ɢʙᴀɴ", callback_data="help_callback hb13"),
            ],
            [
                InlineKeyboardButton(text="ɢʟᴏʙᴀʟ", callback_data="help_callback hb14"),
                InlineKeyboardButton(text="ᴇxᴛʀᴀ", callback_data="help_callback hb15"),
                InlineKeyboardButton(text="sᴏɴɢ", callback_data="help_callback hb16"),
            ],
            [
                InlineKeyboardButton(text="◁ ʙᴀᴄᴋ", callback_data="help_callback hb_page1"), # Wapas Page 1 par
                InlineKeyboardButton(text="ɴᴇxᴛ ▷", callback_data="help_callback hb_page3"), # Page 3 par
            ],
        ]
    )
    return upl

# --- PAGE 3 (Ye bhi missing tha) ---
def help_pannel_3(_, START: Union[bool, int] = None):
    upl = InlineKeyboardMarkup(
        [
            [
                InlineKeyboardButton(text="sᴘᴇᴇᴅ", callback_data="help_callback hb17"),
                InlineKeyboardButton(text="sᴛᴀᴛs", callback_data="help_callback hb18"),
            ],
            [
                InlineKeyboardButton(text="◁ ʙᴀᴄᴋ", callback_data="help_callback hb_page2"), # Wapas Page 2 par
                InlineKeyboardButton(text="ᴄʟᴏsᴇ ✘", callback_data="close"),
            ],
        ]
    )
    return upl

def help_back_markup(_):
    upl = InlineKeyboardMarkup(
        [
            [
                InlineKeyboardButton(
                    text="◁ ʙᴀᴄᴋ",
                    callback_data=f"settingsback_helper",
                ),
                InlineKeyboardButton(
                    text="ᴄʟᴏsᴇ ✘", callback_data=f"close"
                )
            ]
        ]
    )
    return upl

def private_help_panel(_):
    buttons = [
        [
            InlineKeyboardButton(
                text="ʜᴇʟᴘ 💡",
                callback_data="settings_helper",
            ),
        ],
    ]
    return buttons
