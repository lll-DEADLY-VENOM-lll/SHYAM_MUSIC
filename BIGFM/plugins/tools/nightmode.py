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
import config

# --- DATABASE LOGIC ---
nightdb = mongodb.nightmode
served_chats_db = mongodb.Yukki.served_chats 

async def is_global_nightmode_on() -> bool:
    check = await nightdb.find_one({"chat_id": "GLOBAL"})
    return bool(check)

async def global_nightmode_on():
    return await nightdb.update_one(
        {"chat_id": "GLOBAL"}, {"$set": {"status": "ON"}}, upsert=True
    )

async def global_nightmode_off():
    return await nightdb.delete_one({"chat_id": "GLOBAL"})

# --- OWNER CHECK ---
def is_owner(user_id):
    owners = config.OWNER_ID
    if isinstance(owners, int):
        return user_id == owners
    elif isinstance(owners, list):
        return user_id in owners
    return False

# --- PERMISSIONS ---
CLOSE_CHAT = ChatPermissions(can_send_messages=False)
OPEN_CHAT = ChatPermissions(can_send_messages=True)

# --- BUTTONS ---
buttons = InlineKeyboardMarkup(
    [[
        InlineKeyboardButton("๏ ᴇɴᴀʙʟᴇ ๏", callback_data="global_on"),
        InlineKeyboardButton("๏ ᴅɪsᴀʙʟᴇ ๏", callback_data="global_off"),
    ]]
)

add_buttons = InlineKeyboardMarkup(
    [
        [
            InlineKeyboardButton(
                text="๏ ᴀᴅᴅ ᴍᴇ ɪɴ ɢʀᴏᴜᴘ ๏",
                url=f"https://t.me/{app.username}?startgroup=true",
            )
        ]
    ]
)

# --- COMMAND ---
@app.on_message(filters.command("nightmode") & filters.group)
async def _nightmode(_, message: Message):
    if not is_owner(message.from_user.id):
        return await message.reply_text("❌ **Sɪʀғ Mᴇʀᴇ Mᴀʟɪᴋ (Bᴏᴛ Oᴡɴᴇʀ) ʜɪ ɴɪɢʜᴛᴍᴏᴅᴇ ᴄᴏɴᴛʀᴏʟ ᴋᴀʀ sᴀᴋᴛᴇ ʜᴀɪɴ.**")

    status = "Enabled ✅" if await is_global_nightmode_on() else "Disabled ❌"
    await message.reply_photo(
        photo="https://telegra.ph//file/06649d4d0bbf4285238ee.jpg",
        caption=f"**ɢʟᴏʙᴀʟ ɴɪɢʜᴛᴍᴏᴅᴇ Sᴇᴛᴛɪɴɢs**\n\n**Cᴜʀʀᴇɴᴛ Sᴛᴀᴛᴜs:** {status}\n\nAbhi Enable karne par bot saare groups ko raat 12 baje band kar dega.",
        reply_markup=buttons,
    )

# --- CALLBACK ---
@app.on_callback_query(filters.regex("^(global_on|global_off)$"))
async def nightcb(_, query: CallbackQuery):
    if not is_owner(query.from_user.id):
        return await query.answer("Sirf Bot Owner ke liye hai!", show_alert=True)

    if query.data == "global_on":
        await global_nightmode_on()
        await query.message.edit_caption("**✅ Global Nightmode ON ho gaya hai! Ab saare groups 12AM ko band honge.**", reply_markup=buttons)
    
    elif query.data == "global_off":
        await global_nightmode_off()
        await query.message.edit_caption("**❌ Global Nightmode OFF ho gaya hai!**", reply_markup=buttons)

# --- AUTO FUNCTIONS ---

async def start_nightmode():
    if not await is_global_nightmode_on():
        return

    chats = []
    async for chat in served_chats_db.find({"chat_id": {"$lt": 0}}):
        chats.append(int(chat["chat_id"]))

    for chat_id in chats:
        try:
            await app.send_photo(
                chat_id,
                photo="https://telegra.ph//file/06649d4d0bbf4285238ee.jpg",
                caption="**ᴍᴀʏ ᴛʜᴇ ᴀɴɢᴇʟs ғʀᴏᴍ ʜᴇᴀᴠᴇɴ ʙʀɪɴɢ ᴛʜᴇ sᴡᴇᴇᴛᴇsᴛ ᴏғ ᴀʟʟ ᴅʀᴇᴀᴍs ғᴏʀ ʏᴏᴜ. ᴍᴀʏ ʏᴏᴜ ʜᴀᴠᴇ ʟᴏɴɢ ᴀɴᴅ ʙʟɪssғᴜʟ sʟᴇᴇᴘ ғᴜʟʟ ᴏғ ʜᴀᴘᴘʏ ᴅʀᴇᴀᴍs.\n\nɢʀᴏᴜᴘ ɪs ᴄʟᴏsɪɴɢ ɢᴏᴏᴅ ɴɪɢʜᴛ ᴇᴠᴇʀʏᴏɴᴇ !**",
                reply_markup=add_buttons
            )
            await app.set_chat_permissions(chat_id, CLOSE_CHAT)
        except:
            continue

async def close_nightmode():
    chats = []
    async for chat in served_chats_db.find({"chat_id": {"$lt": 0}}):
        chats.append(int(chat["chat_id"]))

    for chat_id in chats:
        try:
            await app.send_photo(
                chat_id,
                photo="https://telegra.ph//file/14ec9c3ff42b59867040a.jpg",
                caption="**ɢʀᴏᴜᴘ ɪs ᴏᴘᴇɴɪɴɢ ɢᴏᴏᴅ ᴍᴏʀɴɪɴɢ ᴇᴠᴇʀʏᴏɴᴇ !\n\nᴍᴀʏ ᴛʜɪs ᴅᴀʏ ᴄᴏᴍᴇ ᴡɪᴛʜ ᴀʟʟ ᴛʜᴇ ʟᴏᴠᴇ ʏᴏᴜʀ ʜᴇᴀʀᴛ ᴄᴀɴ ʜᴏʟᴅ ᴀɴᴅ ʙʀɪɴɢ ʏᴏᴜ ᴇᴠᴇʀʏ sᴜᴄᴄᴇss ʏᴏᴜ ᴅᴇsɪʀᴇ. Mᴀʏ ᴇᴀᴄʜ ᴏғ ʏᴏᴜʀ ғᴏᴏᴛsᴛᴇᴘs ʙʀɪɴɢ Jᴏʏ ᴛᴏ ᴛʜᴇ ᴇᴀʀᴛʜ ᴀɴᴅ ʏᴏᴜʀsᴇʟғ. ɪ ᴡɪsʜ ʏᴏᴜ ᴀ ᴍᴀɢɪᴄᴀʟ ᴅᴀʏ ᴀɴᴅ ᴀ ᴡᴏɴᴅᴇʀғᴜʟ ʟɪғᴇ ᴀʜᴇᴀᴅ.**",
                reply_markup=add_buttons
            )
            await app.set_chat_permissions(chat_id, OPEN_CHAT)
        except:
            continue

# --- SCHEDULER ---
scheduler = AsyncIOScheduler(timezone="Asia/Kolkata")
scheduler.add_job(start_nightmode, trigger="cron", hour=0, minute=0)
scheduler.add_job(close_nightmode, trigger="cron", hour=6, minute=0)
scheduler.start()
