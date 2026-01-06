import sys
import config
from pyrogram import filters
from pyrogram.types import InlineKeyboardButton, InlineKeyboardMarkup, CallbackQuery
from BIGFM import app

# --- 🔐 CREDIT PROTECTION LOGIC (FIXED) ---
MASTER_DEV = "кιяυ"  # Isse aur niche wale checks ko SAME hona chahiye

def get_about_text():
    # Security check fix
    DEV_NAME = "кιяυ" 
    
    if DEV_NAME != MASTER_DEV:
        return "⚠️ **sʏsᴛᴇᴍ ᴇʀʀᴏʀ:** sᴏᴍᴇᴛʜɪɴɢ ɪs ᴍɪssɪɴɢ!\n\nᴄʀᴇᴅɪᴛs ᴛᴀᴍᴘᴇʀᴇᴅ. ᴘʟᴇᴀsᴇ ʀᴇɪɴsᴛᴀʟʟ ᴛʜᴇ ᴏʀɪɢɪɴᴀʟ ʙᴏᴛ."

    return f"""
🎧 **sσηᴧʟɪ ϻυsɪᴄ [ ησ ᴧᴅs ]**
*ʏᴏᴜʀ ᴘᴇʀsᴏɴᴀʟ ᴅᴊ ᴏɴ ᴛᴇʟᴇɢʀᴀᴍ*

ᴇɴᴊᴏʏ sᴍᴏᴏᴛʜ ᴘʟᴀʏʙᴀᴄᴋ, ᴀᴅᴠᴀɴᴄᴇᴅ ᴄᴏɴᴛʀᴏʟs, ᴀɴᴅ ᴀ ᴘʀᴇᴍɪᴜᴍ ᴀᴜᴅɪᴏ ᴇxᴘᴇʀɪᴇɴᴄᴇ ᴡɪᴛʜᴏᴜᴛ ᴀ sɪɴɢʟᴇ ᴀᴅ.

**◈ ǫᴜɪᴄᴋ ɪɴғᴏ ◈**
╰ ᴠᴇʀsɪᴏɴ : 𝟷.𝟶.𝟶
╰ ᴅᴇᴠ : [ {MASTER_DEV} ](https://t.me/KIRU_OP) 
╰ sᴜᴘᴘᴏʀᴛ : [ᴜᴘᴅᴀᴛᴇs]({getattr(config, 'SUPPORT_CHANNEL', 'https://t.me/about_deadly_venom')})
╰ sᴛᴀᴛᴜs : ᴘᴜʙʟɪᴄ ʀᴇʟᴇᴀsᴇ

── sɪɴᴄᴇ 𝟶𝟷.𝟶𝟷.𝟸𝟶𝟸𝟶 ──
"""

# --- 📱 START PANEL (Missing Function Fix) ---
def start_panel(_):
    buttons = [
        [
            InlineKeyboardButton(
                text="➕ ᴀᴅᴅ ᴍᴇ ᴛᴏ ʏᴏᴜʀ ɢʀᴏᴜᴘ ➕",
                url=f"https://t.me/{app.username}?startgroup=true",
            )
        ],
        [
            InlineKeyboardButton(text="💬 sᴜᴘᴘᴏʀᴛ", url=config.SUPPORT_GROUP),
            InlineKeyboardButton(text="ᴜᴘᴅᴀᴛᴇs 📢", url=config.SUPPORT_CHANNEL),
        ],
    ]
    return buttons

# --- 📱 PRIVATE PANEL (1-2-2-1 Format) ---
def private_panel(_):
    buttons = [
        [
            InlineKeyboardButton(
                text="➕ ᴀᴅᴅ ᴍᴇ ɪɴ ʏᴏᴜʀ ɢʀᴏᴜᴘ ➕",
                url=f"https://t.me/{app.username}?startgroup=true",
            )
        ],
        [
            InlineKeyboardButton(text="💬 sᴜᴘᴘᴏʀᴛ ↗️", url=config.SUPPORT_GROUP),
            InlineKeyboardButton(text="ɴᴇᴡs 📰 ↗️", url=config.SUPPORT_CHANNEL),
        ],
        [
            InlineKeyboardButton(text="📜 ᴘʀɪᴠᴀᴄʏ", url="https://telegra.ph/Privacy-Policy"),
            InlineKeyboardButton(text="ᴀʙᴏᴜᴛ ℹ️", callback_data="about_callback"),
        ],
        [
            InlineKeyboardButton(
                text="📖 ʜᴇʟᴘ ᴀɴᴅ ᴄᴏᴍᴍᴀɴᴅ's 📖", 
                callback_data="settings_back_helper"
            )
        ],
    ]
    return buttons

# --- 🚀 STARTUP SECURITY CHECK ---
if MASTER_DEV != "кιяυ":
    print("FATAL ERROR: Developer credits missing in code!")
    sys.exit() # Ab credits match hain, toh bot start ho jayega
