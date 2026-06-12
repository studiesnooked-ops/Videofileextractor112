"""
Telegram Video Extractor Bot for Render
"""

import os
import re
import yt_dlp
import requests
import subprocess
from flask import Flask, request
from pyrogram import Client, filters
from multiprocessing import Process

# Flask app for web service
app = Flask(__name__)

# ===== ENVIRONMENT =====
API_ID = int(os.getenv("API_ID"))
API_HASH = os.getenv("API_HASH")
BOT_TOKEN = os.getenv("BOT_TOKEN")
OWNER_ID = int(os.getenv("OWNER_ID", "0"))
SUDO_USERS = [int(x) for x in os.getenv("SUDO_USERS", "").split() if x]
SUDO_USERS.append(OWNER_ID)

# Downloads folder
DOWNLOADS_DIR = "downloads"
os.makedirs(DOWNLOADS_DIR, exist_ok=True)

# ===== PYROGRAM BOT =====
pyrogram_bot = Client(
    "saini_bot",
    api_id=API_ID,
    api_hash=API_HASH,
    bot_token=BOT_TOKEN
)

# ===== HELPER FUNCTIONS =====
def clean_filename(title):
    name = re.sub(r'[^\w\s-]', '', title).strip()[:50]
    return name.replace(' ', '_')

def is_classx(url):
    return any(x in url.lower() for x in ['classx', 'appxapi', 'clsx'])

def is_m3u8(url):
    return '.m3u8' in url.lower()

def is_pdf(url):
    return url.lower().endswith('.pdf') or '/pdf' in url.lower()

def is_video(url):
    sites = ['youtube.com', 'youtu.be', 'instagram.com', 'tiktok.com', 'facebook.com']
    return any(x in url.lower() for x in sites)

# ===== DOWNLOADERS =====
def download_video(url, title):
    try:
        safe_name = clean_filename(title)
        output = os.path.join(DOWNLOADS_DIR, f"{safe_name}.mp4")
        
        ydl_opts = {
            'format': 'best[ext=mp4]/best',
            'outtmpl': output,
            'quiet': True,
            'no_warnings': True,
        }
        
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            ydl.download([url])
        
        if os.path.exists(output):
            return output
        
        # Find downloaded file
        for f in os.listdir(DOWNLOADS_DIR):
            full = os.path.join(DOWNLOADS_DIR, f)
            if os.path.isfile(full) and f.endswith('.mp4'):
                return full
        return None
    except Exception as e:
        print(f"[VIDEO ERROR] {e}")
        return None

def download_m3u8(url, title):
    try:
        safe_name = clean_filename(title)
        output = os.path.join(DOWNLOADS_DIR, f"{safe_name}.mp4")
        
        cmd = ['ffmpeg', '-i', url, '-c', 'copy', '-y', output]
        result = subprocess.run(cmd, capture_output=True, timeout=300)
        
        if os.path.exists(output):
            return output
        return None
    except Exception as e:
        print(f"[M3U8 ERROR] {e}")
        return None

def download_file(url, title):
    try:
        safe_name = clean_filename(title)
        ext = '.pdf' if url.lower().endswith('.pdf') else '.mp4'
        output = os.path.join(DOWNLOADS_DIR, f"{safe_name}{ext}")
        
        r = requests.get(url, timeout=60, stream=True)
        if r.status_code == 200:
            with open(output, 'wb') as f:
                for chunk in r.iter_content(8192):
                    if chunk:
                        f.write(chunk)
            return output if os.path.exists(output) else None
        return None
    except Exception as e:
        print(f"[FILE ERROR] {e}")
        return None

def get_classx_url(api_url):
    try:
        r = requests.get(api_url, timeout=15)
        if r.status_code == 200:
            try:
                data = r.json()
                for key in ['url', 'video_url', 'm3u8', 'stream_url', 'playUrl']:
                    if key in data and data[key]:
                        return data[key]
            except:
                return api_url if api_url.startswith('http') else None
        return None
    except Exception as e:
        print(f"[CLASSX ERROR] {e}")
        return None

# ===== ACCESS CHECK =====
def has_access(user_id):
    return user_id in SUDO_USERS or user_id == OWNER_ID

# ===== PYROGRAM HANDLERS =====
@pyrogram_bot.on_message(filters.command("start"))
async def start_cmd(client, msg):
    if has_access(msg.from_user.id):
        await msg.reply_text("✅ Bot Working!\n\nSend me a .txt file with links.")

@pyrogram_bot.on_message(filters.command("ping"))
async def ping_cmd(client, msg):
    if has_access(msg.from_user.id):
        await msg.reply_text("pong 🏓")

@pyrogram_bot.on_message(filters.document)
async def handle_txt(client, msg):
    user_id = msg.from_user.id
    
    if not has_access(user_id):
        await msg.reply_text("❌ Unauthorized")
        return
    
    if msg.document.file_name and not msg.document.file_name.endswith('.txt'):
        await msg.reply_text("❌ Send only .txt file")
        return
    
    txt_path = None
    try:
        status = await msg.reply_text("📥 Processing...")
        
        txt_path = await msg.download()
        
        with open(txt_path, 'r', encoding='utf-8') as f:
            lines = f.readlines()
        
        # Parse links
        links = []
        for line in lines:
            line = line.strip()
            if ':' in line:
                title = line.split(':', 1)[0].strip()
                url = line.split(':', 1)[1].strip()
                if url.startswith('http'):
                    links.append((title, url))
        
        if not links:
            await status.edit_text("❌ No valid links")
            return
        
        await status.edit_text(f"📋 {len(links)} links found")
        
        success = 0
        failed = 0
        
        for i, (title, url) in enumerate(links, 1):
            await status.edit_text(f"⬇️ [{i}/{len(links)}]\n{title}")
            
            downloaded = None
            
            try:
                if is_classx(url):
                    stream_url = get_classx_url(url)
                    if stream_url:
                        downloaded = download_m3u8(stream_url, title) if '.m3u8' in stream_url else download_file(stream_url, title)
                    else:
                        downloaded = download_m3u8(url, title) if is_m3u8(url) else download_file(url, title)
                
                elif is_m3u8(url):
                    downloaded = download_m3u8(url, title)
                
                elif is_pdf(url):
                    downloaded = download_file(url, title)
                
                elif is_video(url):
                    downloaded = download_video(url, title)
                
                else:
                    downloaded = download_video(url, title) or download_file(url, title)
                
                if downloaded and os.path.exists(downloaded):
                    if downloaded.endswith('.pdf'):
                        await msg.reply_document(document=downloaded, caption=f"📄 {title}")
                    else:
                        await msg.reply_video(video=downloaded, caption=f"🎬 {title}")
                    
                    try:
                        os.remove(downloaded)
                    except:
                        pass
                    
                    success += 1
                else:
                    await msg.reply_text(f"❌ Failed: {title}")
                    failed += 1
                    
            except Exception as e:
                print(f"[ERROR] {e}")
                await msg.reply_text(f"❌ Error: {title}")
                failed += 1
        
        await status.edit_text(f"✅ Done!\nSuccess: {success}\nFailed: {failed}")
    
    except Exception as e:
        print(f"[MAIN ERROR] {e}")
        await msg.reply_text(f"❌ Error: {str(e)[:200]}")
    
    finally:
        if txt_path and os.path.exists(txt_path):
            try:
                os.remove(txt_path)
            except:
                pass

# ===== FLASK ROUTES =====
@app.route('/')
def home():
    return "Bot is running! 🔥"

@app.route('/health')
def health():
    return {"status": "ok", "bot": "running"}

# ===== RUN FUNCTIONS =====
def run_flask():
    print("🚀 Starting Flask...")
    app.run(host='0.0.0.0', port=int(os.getenv("PORT", 5000)))

def run_pyrogram():
    print("🤖 Starting Pyrogram...")
    pyrogram_bot.run()

if __name__ == "__main__":
    # Run both Flask and Pyrogram
    flask_process = Process(target=run_flask)
    pyrogram_process = Process(target=run_pyrogram)
    
    flask_process.start()
    pyrogram_process.start()
    
    flask_process.join()
    pyrogram_process.join()
