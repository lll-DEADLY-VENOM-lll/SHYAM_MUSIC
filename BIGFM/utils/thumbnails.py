import os
import re
import aiofiles
import aiohttp
from PIL import Image, ImageDraw, ImageEnhance, ImageFilter, ImageFont
# Yahan badlav kiya gaya hai:
from youtubesearchpython.__future__ import VideosSearch 

from config import YOUTUBE_IMG_URL

# ... baaki ka code waisa hi rahega ...
# Image resize karne ke liye helper function
def resize_image(image, width, height):
    return image.resize((width, height), Image.LANCZOS)

async def get_thumb(videoid):
    cache_path = f"cache/{videoid}.png"
    temp_path = f"cache/thumb{videoid}.png"
    
    if os.path.isfile(cache_path):
        return cache_path

    url = f"https://www.youtube.com/watch?v={videoid}"
    try:
        results = VideosSearch(url, limit=1)
        res_data = await results.next()
        
        if not res_data["result"]:
            return YOUTUBE_IMG_URL

        result = res_data["result"][0]
        title = re.sub(r"\W+", " ", result.get("title", "Unsupported Title")).title()
        duration = result.get("duration", "Unknown")
        thumbnail = result["thumbnails"][0]["url"].split("?")[0]
        views = result.get("viewCount", {}).get("short", "Unknown Views")

        # Download thumbnail
        async with aiohttp.ClientSession() as session:
            async with session.get(thumbnail) as resp:
                if resp.status == 200:
                    async with aiofiles.open(temp_path, mode="wb") as f:
                        await f.write(await resp.read())

        # Process Image
        youtube = Image.open(temp_path).convert("RGBA")
        
        # Colors
        GLOW_COLOR = "#ff0099" 
        BORDER_COLOR = "#FF1493"

        # Background Setup (Blurred)
        bg = resize_image(youtube, 1280, 720)
        bg = bg.filter(ImageFilter.GaussianBlur(25))
        bg = ImageEnhance.Brightness(bg).enhance(0.3)

        # Main Thumbnail Setup
        thumb_width, thumb_height = 840, 460
        main_thumb = resize_image(youtube, thumb_width, thumb_height)
        
        # Rounded corners for main thumb
        mask = Image.new("L", (thumb_width, thumb_height), 0)
        draw_mask = ImageDraw.Draw(mask)
        draw_mask.rounded_rectangle([(0, 0), (thumb_width, thumb_height)], radius=25, fill=255)
        main_thumb.putalpha(mask)

        # Positions
        center_x, center_y = 640, 320
        thumb_x = center_x - (thumb_width // 2)
        thumb_y = center_y - (thumb_height // 2)

        # Glow Effect
        glow_layer = Image.new("RGBA", (1280, 720), (0, 0, 0, 0))
        draw_glow = ImageDraw.Draw(glow_layer)
        draw_glow.rounded_rectangle(
            [(thumb_x - 15, thumb_y - 15), (thumb_x + thumb_width + 15, thumb_y + thumb_height + 15)],
            radius=35, fill=GLOW_COLOR
        )
        glow_layer = glow_layer.filter(ImageFilter.GaussianBlur(20))
        bg.paste(glow_layer, (0, 0), glow_layer)

        # Border
        border_layer = Image.new("RGBA", (1280, 720), (0, 0, 0, 0))
        draw_border = ImageDraw.Draw(border_layer)
        draw_border.rounded_rectangle(
            [(thumb_x - 5, thumb_y - 5), (thumb_x + thumb_width + 5, thumb_y + thumb_height + 5)],
            radius=30, fill=BORDER_COLOR
        )
        bg.paste(border_layer, (0, 0), border_layer)

        # Paste Main Thumbnail
        bg.paste(main_thumb, (thumb_x, thumb_y), main_thumb)

        # Drawing Text
        draw = ImageDraw.Draw(bg)
        
        # Font Loading
        try:
            font_title = ImageFont.truetype("BIGFM/assets/font.ttf", 45)
            font_details = ImageFont.truetype("BIGFM/assets/font2.ttf", 30)
            font_wm = ImageFont.truetype("BIGFM/assets/font2.ttf", 25)
        except:
            font_title = ImageFont.load_default()
            font_details = ImageFont.load_default()
            font_wm = ImageFont.load_default()

        # Title Handling
        if len(title) > 40:
            title = title[:37] + "..."

        # Text Centering Logic (Pillow 10+ compatible)
        def get_text_center(text, font, img_w):
            bbox = draw.textbbox((0, 0), text, font=font)
            return (img_w - (bbox[2] - bbox[0])) / 2

        # Draw Title
        title_x = get_text_center(title, font_title, 1280)
        draw.text((title_x, 580), title, fill="white", font=font_title, stroke_width=2, stroke_fill="black")

        # Draw Stats
        stats_text = f"Views: {views} | Duration: {duration} | Bot: @aashikmusicbot"
        stats_x = get_text_center(stats_text, font_details, 1280)
        draw.text((stats_x, 640), stats_text, fill=BORDER_COLOR, font=font_details)

        # Watermarks
        draw.text((30, 30), "AloneMusic", fill="yellow", font=font_wm, stroke_width=1, stroke_fill="black")
        draw.text((1120, 680), "AloneMusic", fill="white", font=font_wm, alpha=150)

        # Clean up and Save
        if os.path.exists(temp_path):
            os.remove(temp_path)
            
        bg.convert("RGB").save(cache_path, "PNG")
        return cache_path

    except Exception as e:
        print(f"Error generating thumbnail: {e}")
        return YOUTUBE_IMG_URL

async def get_qthumb(vidid):
    try:
        url = f"https://www.youtube.com/watch?v={vidid}"
        results = VideosSearch(url, limit=1)
        res_data = await results.next()
        return res_data["result"][0]["thumbnails"][0]["url"].split("?")[0]
    except Exception:
        return YOUTUBE_IMG_URL
