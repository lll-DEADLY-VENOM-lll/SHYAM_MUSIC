import logging
from apscheduler.schedulers.asyncio import AsyncIOScheduler
from pyrogram import enums, filters
from pyrogram.types import (
    CallbackQuery,
    ChatPermissions,
    InlineKeyboardButton,
    InlineKeyboardMarkup,
    Message,
)

# Bot ke imports
from BIGFM import app 
from BIGFM.core.mongo import mongodb
from config import OWNER_ID

# --- DATABASE LOGIC ---
nightdb = mongodb.nightmode

async def get_nightchats() -> list:
    chats = nightdb.find({"chat_id": {"$lt": 0}})
    chats_list = []
    async for chat in chats:
        chats_list.append(chat)
    return chats_list

async def nightmode_on(chat_id: int):
    return await nightdb.insert_one({"chat_id": chat_id})

async def nightmode_off(chat_id: int):
    return await nightdb.delete_one({"chat_id": chat_id})

# --- PERMISSIONS ---
CLOSE_CHAT = ChatPermissions(
    can_send_messages=False,
    can_send_media_messages=False,
    can_send_other_messages=False,
    can_send_polls=False,
    can_change_info=False,
    can_add_web_page_previews=False,
    can_pin_messages=False,
    can_invite_users=True,
)

OPEN_CHAT = ChatPermissions(
    can_send_messages=True,
    can_send_media_messages=True,
    can_send_other_messages=True,
    can_send_polls=True,
    can_change_info=True,
    can_add_web_page_previews=True,
    can_pin_messages=True,
    can_invite_users=True,
)

# --- BUTTONS ---
buttons = InlineKeyboardMarkup(
    [[
        InlineKeyboardButton("๏ ᴇɴᴀʙʟᴇ ๏", callback_data="add_night"),
        InlineKeyboardButton("๏ ᴅɪsᴀʙʟᴇ ๏", callback_data="rm_night"),
    ]]
)

# --- COMMAND (SIRF OWNER KE LIYE) ---
# filters.user(OWNER_ID) lagane se sirf owner hi command chala payega
@app.on_message(filters.command("nightmode") & filters.user(OWNER_ID) & filters.group)
async def _nightmode(_, message: Message):
    await message.reply_photo(
        photo="https://telegra.ph//file/06649d4d0bbf4285238ee.jpg",
        caption="**ʜᴇʟʟᴏ Sɪʀ! Cʟɪᴄᴋ ᴛʜᴇ ʙᴜᴛᴛᴏɴ ʙᴇʟᴏᴡ ᴛᴏ ᴄᴏɴᴛʀᴏʟ ɴɪɢʜᴛᴍᴏᴅᴇ ғᴏʀ ᴛʜɪs ᴄʜᴀᴛ.**",
        reply_markup=buttons,
    )

# --- CALLBACK (SIRF OWNER KE LIYE) ---
@app.on_callback_query(filters.regex("^(add_night|rm_night)$"))
async def nightcb(_, query: CallbackQuery):
    if query.from_user.id not in OWNER_ID:
        return await query.answer("Ye power sirf Bot Owner ke paas hai!", show_alert=True)

    chat_id = query.message.chat.id
    check_night = await nightdb.find_one({"chat_id": chat_id})

    if query.data == "add_night":
        if check_night:
            await query.message.edit_caption("**๏ ɴɪɢʜᴛᴍᴏᴅᴇ ɪs ᴀʟʀᴇᴀᴅʏ ᴇɴᴀʙʟᴇᴅ.**")
        else:
            await nightmode_on(chat_id)
            await query.message.edit_caption("**๏ ɴɪɢʜᴛᴍᴏᴅᴇ ᴇɴᴀʙʟᴇᴅ ʙʏ Oᴡɴᴇʀ! [12AM-6AM]**")

    elif query.data == "rm_night":
        if check_night:
            await nightmode_off(chat_id)
            await query.message.edit_caption("**๏ ɴɪɢʜᴛᴍᴏᴅᴇ ᴅɪsᴀʙʟᴇᴅ ʙʏ Oᴡɴᴇʀ.**")
        else:
            await query.message.edit_caption("**๏ ɴɪɢʜᴛᴍᴏᴅᴇ ɪs ᴀʟʀᴇᴀᴅʏ ᴅɪsᴀʙʟᴇᴅ.**")

# --- AUTO FUNCTIONS (NIGHT/MORNING) ---
async def start_nightmode():
    chats = await get_nightchats()
    for chat in chats:
        try:
            chat_id = int(chat["chat_id"])
            await app.send_photo(
                chat_id,
                photo="https://telegra.ph//file/06649d4d0bbf4285238ee.jpg",
                caption="**ᴍᴀʏ ᴛʜᴇ ᴀɴɢᴇʟs ғʀᴏᴍ ʜᴇᴀᴠᴇɴ ʙʀɪɴɢ ᴛʜᴇ sᴡᴇᴇᴛᴇsᴛ ᴏғ ᴀʟʟ ᴅʀᴇᴀᴍs ғᴏʀ ʏᴏᴜ. ᴍᴀʏ ʏᴏᴜ ʜᴀᴠᴇ ʟᴏɴɢ ᴀɴᴅ ʙʟɪssғᴜʟ sʟᴇᴇᴘ ғᴜʟʟ ᴏғ ʜᴀᴘᴘʏ ᴅʀᴇᴀᴍs.\n\nɢʀᴏᴜᴘ ɪs ᴄʟᴏsɪɴɢ ɢᴏᴏᴅ ɴɪɢʜᴛ ᴇᴠᴇʀʏᴏɴᴇ !**"
            )
            await app.set_chat_permissions(chat_id, CLOSE_CHAT)
        except:
            continue

async def close_nightmode():
    chats = await get_nightchats()
    for chat in chats:
        try:
            chat_id = int(chat["chat_id"])
            await app.send_photo(
                chat_id,
                photo="https://telegra.ph//file/14ec9c3ff42b59867040a.jpg",
                caption="**ɢʀᴏᴜᴘ ɪs ᴏᴘᴇɴɪɴɢ ɢᴏᴏᴅ ᴍᴏʀɴɪɴɢ ᴇᴠᴇʀʏᴏɴᴇ !\n\nᴍᴀʏ ᴛʜɪs ᴅᴀʏ ᴄᴏᴍᴇ ᴡɪᴛʜ ᴀʟʟ ᴛʜᴇ ʟᴏᴠᴇ ʏᴏᴜʀ ʜᴇᴀʀᴛ ᴄᴀɴ ʜᴏʟᴅ ᴀɴᴅ ʙʀɪɴɢ ʏᴏᴜ ᴇᴠᴇʀʏ sᴜᴄᴄᴇss ʏᴏᴜ ᴅᴇsɪʀᴇ. Mᴀʏ ᴇᴀᴄʜ ᴏғ ʏᴏᴜʀ ғᴏᴏᴛsᴛᴇᴘs ʙʀɪɴɢ Jᴏʏ ᴛᴏ ᴛʜᴇ ᴇᴀʀᴛʜ ᴀɴᴅ ʏᴏᴜʀsᴇʟғ. ɪ ᴡɪsʜ ʏᴏᴜ ᴀ ᴍᴀɢɪᴄᴀʟ ᴅᴀʏ ᴀɴᴅ ᴀ ᴡᴏɴᴅᴇʀғᴜʟ ʟɪғᴇ ᴀʜᴇᴀᴅ.**"
            )
            await app.set_chat_permissions(chat_id, OPEN_CHAT)
        except:
            continue

# --- SCHEDULER ---
scheduler = AsyncIOScheduler(timezone="Asia/Kolkata")
scheduler.add_job(start_nightmode, trigger="cron", hour=0, minute=0) # Raat 12:00 baje
scheduler.add_job(close_nightmode, trigger="cron", hour=6, minute=0) # Subah 06:00 baje
scheduler.start()
