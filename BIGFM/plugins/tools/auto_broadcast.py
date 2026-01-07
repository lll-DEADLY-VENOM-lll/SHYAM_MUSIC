import asyncio
from pyrogram import Client, filters
from BIGFM.utils.database import get_served_chats, get_served_users

# --- SETTINGS ---
# Apni Telegram ID yahan likhein
ADMIN_ID = 6123456789  # <--- Apni ID yahan daalein

# --- PREMIUM MESSAGE ---
BROADCAST_TEXT = """
<b>✨ sʜʏᴀᴍᴠɪʙᴇ ᴍᴜsɪᴄ ✨</b>
————— 「 @sonalixbot 」 —————

🚀 <b>24/7 Ultra-High Uptime</b>
⚡ <b>Lag-Free Performance</b>
🛡️ <b>No Ads • No Spam</b>
💎 <b>Advanced Features</b>

🎧 <i>Experience High-Fidelity Streaming on Telegram. Fast & Stable.</i>

🚀 <b>Add sʜʏᴀᴍᴠɪʙᴇ ᴍᴜsɪᴄ now and upgrade your group's vibe!</b>

<a href="https://t.me/SHYAMVIBEBOT">🔗 CLICK HERE TO START BOT</a>
<a href="https://t.me/SHYAMVIBEBOT?startgroup=true">➕ ADD ME TO YOUR GROUP</a>
"""

# Yeh check karne ke liye ki broadcast chalu hai ya nahi
IS_RUNNING = False

async def start_broadcasting(client: Client):
    global IS_RUNNING
    while IS_RUNNING:
        print("[INFO]: Auto-Broadcast Shuru Ho Raha Hai...")
        
        # Sabhi IDs nikalna
        all_targets = []
        try:
            chats = await get_served_chats()
            for chat in chats:
                all_targets.append(int(chat["chat_id"]))
            
            users = await get_served_users()
            for user in users:
                all_targets.append(int(user["user_id"]))
        except Exception as e:
            print(f"Database Error: {e}")

        # Unique IDs
        unique_targets = list(set(all_targets))
        
        for target_id in unique_targets:
            if not IS_RUNNING: # Agar beech mein stop kiya jaye
                break
            try:
                await client.send_message(
                    target_id, 
                    BROADCAST_TEXT, 
                    disable_web_page_preview=False
                )
                await asyncio.sleep(3) # Flood wait protection
            except Exception:
                continue
        
        print("[INFO]: Broadcast Khatam! Agla broadcast 6 ghante baad hoga.")
        # 6 Ghante wait karega (6 hours * 3600 seconds)
        await asyncio.sleep(6 * 3600)

@Client.on_message(filters.command("start_ad") & filters.user(ADMIN_ID))
async def start_ad_command(client, message):
    global IS_RUNNING
    if IS_RUNNING:
        return await message.reply_text("⚠️ **Auto-Broadcast pehle se hi chalu hai!**")
    
    IS_RUNNING = True
    await message.reply_text("✅ **Auto-Broadcast (Har 6 Ghante) shuru kar diya gaya hai!**")
    # Background task shuru karna
    asyncio.create_task(start_broadcasting(client))

@Client.on_message(filters.command("stop_ad") & filters.user(ADMIN_ID))
async def stop_ad_command(client, message):
    global IS_RUNNING
    if not IS_RUNNING:
        return await message.reply_text("⚠️ **Broadcast abhi chalu nahi hai.**")
    
    IS_RUNNING = False
    await message.reply_text("🛑 **Auto-Broadcast ko agle loop se rok diya jayega.**")
