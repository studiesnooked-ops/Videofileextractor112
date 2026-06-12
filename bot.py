import os
import re
import yt_dlp
import requests
import subprocess
from flask import Flask
from pyrogram import Client, filters
from multiprocessing import Process

app = Flask(__name__)

# Environment Variables
API_ID = int(os.getenv("API_ID"))
API_HASH = os.getenv("API_HASH")
BOT_TOKEN = os.getenv("BOT_TOKEN")
OWNER_ID = int(os.getenv("OWNER_ID", "0"))
SUDO_USERS = [int(x) for x in os.getenv("SUDO_USERS", "").split() if x]
SUDO_USERS.append(OWNER_ID)

DOWNLOADS_DIR = "downloads"
os.makedirs(DOWNLOADS_DIR, exist_ok=True)

# Pyrogram Bot
bot = Client("saini_bot", api_id=API_ID, api_hash=API_HASH, bot_token=BOT_TOKEN)

def clean_filename(title):
    return re.sub(r'[^\w\s-]', '', title).strip()[:50].replace(' ', '_')

def has_access(user_id):
    return user_id in SUDO_USERS or user_id == OWNER_ID

def is_classx(url):
    return any(x in url.lower() for x in ['classx', 'appxapi', 'clsx'])

def is_m3u8(url):
    return '.m3u8' in url.lower()

def is_pdf(url):
    return url.lower().endswith('.pdf') or '/pdf' in url.lower()

def is_video(url):
    sites = ['youtube.com', 'youtu.be', 'instagram.com', 'tiktok.com', 'facebook.com']
    return any(x in url.lower() for x in sites)

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
        
        return output if os.path.exists(output) else None
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

@bot.on_message(filters.command("start"))
async def start_cmd(client, msg):
    if has_access(msg.from_user.id):
        await msg.reply_text("✅ Bot Working!")

@bot.on_message(filters.document)
async def handle_txt(client, msg):
    user_id = msg.from_user.id
    
    if not has_access(user_id):
        await msg.reply_text("❌ Unauthorized")
        return
    
    if msg.document.file_name and not msg.document.file_name.endswith('.txt'):
        await msg.reply_text("❌ Send .txt file only")
        return
    
    txt_path = None
    try:
        status = await msg.reply_text("📥 Processing...")
        
        txt_path = await msg.download()
        
        with open(txt_path, 'r', encoding='utf-8') as f:
            lines = f.readlines()
        
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
            await status.edit_text(f"⬇️ [{i}/{len(links)}] {title}")
            
            downloaded = None
            
            try:
                if is_classx(url):
                    stream_url = get_classx_url(url)
                    downloaded = (download_m3u8(stream_url, title) if stream_url and '.m3u8' in stream_url else download_file(stream_url, title)) if stream_url else None
                
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
        
        await status.edit_text(f"✅ Done! Success: {success}, Failed: {failed}")
    
    except Exception as e:
        print(f"[MAIN ERROR] {e}")
        await msg.reply_text(f"❌ Error: {str(e)[:200]}")
    
    finally:
        if txt_path and os.path.exists(txt_path):
            try:
                os.remove(txt_path)
            except:
                pass

@app.route('/')
def home():
    return "Bot Running! 🔥"

@app.route('/health')
def health():
    return {"status": "ok"}

def run_flask():
    app.run(host='0.0.0.0', port=int(os.getenv("PORT", 8080)))

def run_bot():
    bot.run()

if __name__ == "__main__":
    p1 = Process(target=run_flask)
    p2 = Process(target=run_bot)
    
    p1.start()
    p2.start()
    
    p1.join()
    p2.join()
