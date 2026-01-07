import asyncio
from pyrogram import Client, filters
from apscheduler.schedulers.asyncio import AsyncioScheduler

# BIGFM ke database functions ko import kar rahe hain
from BIGFM.utils.database import get_served_chats, get_served_users

# --- PREMIUM MESSAGE (Sonali Music) ---
BROADCAST_TEXT = """
<b>✨ 𝐒𝐎𝐍𝐀𝐋𝐈 𝐌𝐔𝐒𝐈𝐂 𝐏𝐑𝐄𝐌𝐈𝐔𝐌 ✨</b>
————— 「 @sonalixbot 」 —————

🚀 <b>24/7 Ultra-High Uptime</b>
Hamesha active, har pal aapke liye taiyaar.

⚡ <b>Lag-Free Performance</b>
Zero lag, seamless playback experience.

🛡️ <b>No Ads • No Spam</b>
Pure & Ad-Free environment.

💎 <b>Advanced Features</b>
High-Fidelity (Hi-Fi) Streaming quality.

🚀 <b>Add Sonali Music now and upgrade your group's vibe!</b>

<a href="https://t.me/sonalixbot">🔗 CLICK HERE TO START BOT</a>
<a href="https://t.me/sonalixbot?startgroup=true">➕ ADD ME TO YOUR GROUP</a>
"""

scheduler = AsyncioScheduler()

async def auto_broadcast_bigfm(client: Client):
    """Groups aur DMs dono mein automatically message bhejega"""
    print("[INFO]: BIGFM Auto-Broadcast Shuru Ho Raha Hai...")
    
    # Sabhi IDs nikalna
    all_targets = []
    
    # 1. Groups fetch karna
    try:
        chats = await get_served_chats()
        for chat in chats:
            all_targets.append(int(chat["chat_id"]))
    except Exception as e:
        print(f"Chats fetch karne mein error: {e}")

    # 2. Users (DMs) fetch karna
    try:
        users = await get_served_users()
        for user in users:
            all_targets.append(int(user["user_id"]))
    except Exception as e:
        print(f"Users fetch karne mein error: {e}")

    # Duplicate IDs hatana
    unique_targets = list(set(all_targets))
    
    success = 0
    for target_id in unique_targets:
        try:
            await client.send_message(
                target_id, 
                BROADCAST_TEXT, 
                disable_web_page_preview=False
            )
            success += 1
            # Flood wait se bachne ke liye gap (3 sec)
            await asyncio.sleep(3) 
        except Exception:
            continue
            
    print(f"[INFO]: Broadcast Done! Total: {success} jagahon par bheja gaya.")

# --- COMMANDS ---

@Client.on_message(filters.command("start_ad") & filters.user([YOUR_ADMIN_ID]))
async def start_auto_ad(client, message):
    if not scheduler.running:
        # Har 6 ghante (hours=6) ke liye set
        scheduler.add_job(auto_broadcast_bigfm, "interval", hours=6, args=[client])
        scheduler.start()
        await message.reply_text("✅ **BIGFM: Auto-Broadcast har 6 ghante ke liye start ho gaya hai!**")
    else:
        await message.reply_text("⚠️ **Scheduler pehle se hi chal raha hai.**")

@Client.on_message(filters.command("stop_ad") & filters.user([YOUR_ADMIN_ID]))
async def stop_auto_ad(client, message):
    if scheduler.running:
        scheduler.shutdown()
        await message.reply_text("🛑 **Auto-Broadcast band kar diya gaya hai.**")
    else:
        await message.reply_text("⚠️ **Scheduler chalu nahi hai.**")