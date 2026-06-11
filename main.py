"""
Enhanced Telegram Bot with ClassX Support
Downloads from YouTube, Instagram, TikTok, and ClassX courses
"""

import os
import yt_dlp
import requests
import subprocess
from pyrogram import Client, filters
from vars import API_ID, API_HASH, BOT_TOKEN

# Initialize bot
app = Client(
    "media_downloader_bot",
    api_id=API_ID,
    api_hash=API_HASH,
    bot_token=BOT_TOKEN
)

# Setup downloads directory
DOWNLOADS_DIR = "downloads"
os.makedirs(DOWNLOADS_DIR, exist_ok=True)


class URLProcessor:
    """Process different types of URLs"""
    
    @staticmethod
    def is_classx_url(url):
        """Check if URL is from ClassX API"""
        return "appxapi.vercel.app" in url or "classx.co.in" in url
    
    @staticmethod
    def is_video_url(url):
        """Check if URL is a video (YouTube, Instagram, TikTok, etc)"""
        video_domains = [
            'youtube.com', 'youtu.be',
            'instagram.com', 'tiktok.com',
            'facebook.com', 'twitter.com', 'x.com',
            'dailymotion.com', 'vimeo.com'
        ]
        return any(domain in url for domain in video_domains)
    
    @staticmethod
    def extract_m3u8_url(api_url):
        """Extract m3u8 URL from ClassX API"""
        try:
            response = requests.get(api_url, timeout=10)
            
            if response.status_code == 200:
                try:
                    data = response.json()
                    
                    for key in ['url', 'video_url', 'm3u8', 'stream_url', 'playUrl']:
                        if key in data:
                            return data[key]
                    
                    if isinstance(data, dict):
                        return URLProcessor._find_url_in_dict(data)
                
                except:
                    if 'm3u8' in response.text:
                        return api_url
            
            return None
        except:
            return None
    
    @staticmethod
    def _find_url_in_dict(data, depth=0):
        """Recursively find URL in dictionary"""
        if depth > 5:
            return None
        
        if isinstance(data, dict):
            for key, value in data.items():
                if 'url' in key.lower():
                    if isinstance(value, str) and value.startswith('http'):
                        return value
                result = URLProcessor._find_url_in_dict(value, depth + 1)
                if result:
                    return result
        elif isinstance(data, list):
            for item in data:
                result = URLProcessor._find_url_in_dict(item, depth + 1)
                if result:
                    return result
        
        return None


class Downloader:
    """Download media from various sources"""
    
    @staticmethod
    def download_video_ytdlp(url, title):
        """Download using yt-dlp"""
        try:
            safe_title = "".join(c for c in title if c.isalnum() or c in (' ', '-', '_'))[:50]
            
            ydl_opts = {
                'format': 'best',
                'outtmpl': os.path.join(DOWNLOADS_DIR, f"{safe_title}.%(ext)s"),
                'quiet': False,
                'no_warnings': False
            }
            
            with yt_dlp.YoutubeDL(ydl_opts) as ydl:
                info = ydl.extract_info(url, download=True)
                video_path = ydl.prepare_filename(info)
                return video_path if os.path.exists(video_path) else None
        
        except Exception as e:
            print(f"yt-dlp error: {e}")
            return None
    
    @staticmethod
    def download_m3u8_video(m3u8_url, title):
        """Download m3u8 using ffmpeg"""
        try:
            safe_title = "".join(c for c in title if c.isalnum() or c in (' ', '-', '_'))[:50]
            output_path = os.path.join(DOWNLOADS_DIR, f"{safe_title}.mp4")
            
            cmd = [
                'ffmpeg',
                '-i', m3u8_url,
                '-c', 'copy',
                '-bsf:a', 'aac_adtstoasc',
                output_path,
                '-y'
            ]
            
            result = subprocess.run(cmd, capture_output=True, timeout=600)
            
            if result.returncode == 0 and os.path.exists(output_path):
                return output_path
            return None
        
        except:
            return None
    
    @staticmethod
    def download_pdf(pdf_url, title):
        """Download PDF"""
        try:
            safe_title = "".join(c for c in title if c.isalnum() or c in (' ', '-', '_'))[:50]
            output_path = os.path.join(DOWNLOADS_DIR, f"{safe_title}.pdf")
            
            response = requests.get(pdf_url, timeout=30)
            
            if response.status_code == 200:
                with open(output_path, 'wb') as f:
                    f.write(response.content)
                return output_path
            
            return None
        
        except:
            return None


@app.on_message(filters.command("start"))
async def start_command(client, message):
    """Start command"""
    await message.reply_text(
        "🤖 **Media Downloader Bot**\n\n"
        "Send me a `.txt` file with:\n"
        "✅ YouTube, Instagram, TikTok links\n"
        "✅ ClassX course URLs (m3u8 & PDF)\n"
        "✅ Other video platform links\n\n"
        "Format: `Title : URL`\n"
        "One link per line"
    )


@app.on_message(filters.document)
async def handle_document(client, message):
    """Handle file uploads"""
    
    if message.document.mime_type != "text/plain":
        await message.reply_text("❌ Please send a `.txt` file")
        return
    
    status_msg = await message.reply_text("📥 Processing your file...")
    
    try:
        # Download file
        txt_file_path = await message.download()
        
        with open(txt_file_path, 'r', encoding='utf-8') as f:
            lines = [line.strip() for line in f.readlines() if line.strip()]
        
        if not lines:
            await status_msg.edit_text("❌ File is empty")
            return
        
        await status_msg.edit_text(f"📋 Found {len(lines)} items. Starting download...")
        
        # Process each line
        for idx, line in enumerate(lines, 1):
            try:
                # Parse title and URL
                if ':' not in line:
                    continue
                
                parts = line.split(':', 1)
                title = parts[0].strip()
                url = parts[1].strip()
                
                if not url.startswith('http'):
                    continue
                
                await status_msg.edit_text(f"⬇️ [{idx}/{len(lines)}] {title}")
                
                # Determine URL type and download
                downloaded_file = None
                
                if URLProcessor.is_classx_url(url):
                    # ClassX URL
                    if 'main.m3u8' in url:
                        m3u8_url = URLProcessor.extract_m3u8_url(url)
                        if m3u8_url:
                            downloaded_file = Downloader.download_m3u8_video(m3u8_url, title)
                    
                    elif '.pdf' in url:
                        downloaded_file = Downloader.download_pdf(url, title)
                
                elif URLProcessor.is_video_url(url):
                    # Standard video URL (YouTube, Instagram, etc)
                    downloaded_file = Downloader.download_video_ytdlp(url, title)
                
                else:
                    # Try as direct file
                    downloaded_file = Downloader.download_video_ytdlp(url, title)
                
                # Send downloaded file
                if downloaded_file and os.path.exists(downloaded_file):
                    if downloaded_file.endswith('.pdf'):
                        await message.reply_document(
                            document=downloaded_file,
                            caption=f"📄 {title}"
                        )
                    else:
                        await message.reply_video(
                            video=downloaded_file,
                            caption=f"🎬 {title}"
                        )
                    
                    # Cleanup
                    try:
                        os.remove(downloaded_file)
                    except:
                        pass
                else:
                    await message.reply_text(f"❌ Failed: {title}")
            
            except Exception as e:
                await message.reply_text(f"❌ Error: {str(e)[:100]}")
        
        await status_msg.edit_text("✅ All done!")
    
    except Exception as e:
        await status_msg.edit_text(f"❌ Error: {str(e)[:200]}")
    
    finally:
        # Cleanup
        try:
            if os.path.exists(txt_file_path):
                os.remove(txt_file_path)
        except:
            pass


if __name__ == "__main__":
    print("🤖 Bot is starting...")
    os.makedirs("downloads", exist_ok=True)
    app.run()
