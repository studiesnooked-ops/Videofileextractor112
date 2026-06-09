import os
import sys
import requests
import json
import subprocess
from pyrogram import Client, filters
from pyrogram.types import Message
from vars import API_ID, API_HASH, BOT_TOKEN
import logging

# Setup logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Initialize Pyrogram client
app = Client(
    "media_downloader_bot",
    api_id=API_ID,
    api_hash=API_HASH,
    bot_token=BOT_TOKEN
)

class ContentDownloader:
    """Download content from various sources"""
    
    def __init__(self):
        self.session = requests.Session()
        self.headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36',
            'Referer': 'https://classx.co.in/',
            'Accept': '*/*'
        }
    
    def is_valid_url(self, url):
        """Check if URL is valid"""
        try:
            result = requests.head(url, headers=self.headers, timeout=5)
            return result.status_code < 400
        except:
            return False
    
    def download_m3u8_video(self, url, output_path):
        """Download HLS video using ffmpeg"""
        try:
            cmd = [
                'ffmpeg',
                '-i', url,
                '-c', 'copy',
                '-bsf:a', 'aac_adtstoasc',
                output_path,
                '-loglevel', 'error'
            ]
            
            subprocess.run(cmd, check=True, capture_output=True, timeout=3600)
            return True
        except Exception as e:
            logger.error(f"Video download error: {e}")
            return False
    
    def download_pdf(self, url, output_path):
        """Download PDF file"""
        try:
            response = requests.get(url, headers=self.headers, timeout=60)
            response.raise_for_status()
            
            with open(output_path, 'wb') as f:
                f.write(response.content)
            
            return True
        except Exception as e:
            logger.error(f"PDF download error: {e}")
            return False
    
    def download_from_youtube(self, url, output_path):
        """Download from YouTube using yt-dlp"""
        try:
            import yt_dlp
            
            ydl_opts = {
                'format': 'best',
                'outtmpl': output_path.replace('.mp4', ''),
                'quiet': True,
                'no_warnings': True
            }
            
            with yt_dlp.YoutubeDL(ydl_opts) as ydl:
                ydl.download([url])
            
            return True
        except Exception as e:
            logger.error(f"YouTube download error: {e}")
            return False


downloader = ContentDownloader()


@app.on_message(filters.command("start"))
async def start_command(client: Client, message: Message):
    """Start command"""
    await message.reply_text(
        "🤖 **Welcome to Content Downloader Bot!**\n\n"
        "📝 **How to use:**\n"
        "1. Create a `.txt` file with content URLs (one per line)\n"
        "2. Format: `Title : URL` (optional)\n"
        "3. Send the file to me\n\n"
        "✅ **Supported Content:**\n"
        "• YouTube videos\n"
        "• Course videos (M3U8/HLS)\n"
        "• Course PDF notes\n"
        "• Direct video/audio links\n\n"
        "⚠️ **Important:**\n"
        "• Only download content you have access to\n"
        "• Don't redistribute copyrighted material\n"
        "• Respect platform ToS\n\n"
        "📄 **Example file format:**\n"
        "```\nLecture 1 : https://youtube.com/watch?v=...\n"
        "Notes : https://example.com/notes.pdf\n```"
    )


@app.on_message(filters.document)
async def handle_document(client: Client, message: Message):
    """Handle document uploads"""
    
    # Check if it's a text file
    if message.document.mime_type != "text/plain":
        await message.reply_text("❌ Please send a plain text (.txt) file only!")
        return
    
    status_msg = await message.reply_text("📥 Processing your file...")
    
    # Download the text file
    txt_file_path = await message.download()
    
    try:
        # Read URLs from file
        with open(txt_file_path, 'r') as file:
            lines = file.readlines()
        
        urls_found = len([l for l in lines if l.strip() and ':' in l])
        
        if urls_found == 0:
            await status_msg.edit_text(
                "❌ No valid URLs found!\n\n"
                "Format should be:\n"
                "`Title : URL`"
            )
            return
        
        await status_msg.edit_text(
            f"✅ Found {urls_found} URL(s)\n"
            "⏳ Starting downloads...\n\n"
            "_This may take a while..._"
        )
        
        download_count = 0
        error_count = 0
        
        # Process each URL
        for line_num, line in enumerate(lines, 1):
            line = line.strip()
            
            if not line or ':' not in line:
                continue
            
            try:
                # Parse title and URL
                if ' : ' in line:
                    title, url = line.split(' : ', 1)
                    title = title.strip()
                    url = url.strip()
                else:
                    title = f"Download {line_num}"
                    url = line
                
                await status_msg.edit_text(
                    f"📥 Downloading: {title}\n"
                    f"Progress: {download_count + error_count}/{urls_found}"
                )
                
                # Validate URL
                if not url.startswith('http'):
                    await message.reply_text(f"❌ Invalid URL: {title}")
                    error_count += 1
                    continue
                
                # Create downloads directory
                os.makedirs("downloads", exist_ok=True)
                
                # Determine content type and download
                success = False
                output_file = None
                
                if url.endswith('/main.m3u8'):
                    # ClassX/AppX video (M3U8)
                    logger.info(f"Downloading M3U8 video: {title}")
                    output_file = f"downloads/{title}.mp4"
                    
                    await status_msg.edit_text(
                        f"🎬 Downloading video: {title}\n"
                        f"(This may take several minutes...)\n"
                        f"Progress: {download_count + error_count}/{urls_found}"
                    )
                    
                    success = downloader.download_m3u8_video(url, output_file)
                
                elif url.endswith('.pdf'):
                    # PDF file
                    logger.info(f"Downloading PDF: {title}")
                    output_file = f"downloads/{title}.pdf"
                    
                    await status_msg.edit_text(
                        f"📄 Downloading PDF: {title}\n"
                        f"Progress: {download_count + error_count}/{urls_found}"
                    )
                    
                    success = downloader.download_pdf(url, output_file)
                
                elif 'youtube.com' in url or 'youtu.be' in url:
                    # YouTube video
                    logger.info(f"Downloading YouTube: {title}")
                    output_file = f"downloads/{title}.mp4"
                    
                    await status_msg.edit_text(
                        f"▶️ Downloading YouTube: {title}\n"
                        f"Progress: {download_count + error_count}/{urls_found}"
                    )
                    
                    success = downloader.download_from_youtube(url, output_file)
                
                else:
                    # Try with yt-dlp
                    logger.info(f"Downloading with yt-dlp: {title}")
                    output_file = f"downloads/{title}.mp4"
                    
                    try:
                        import yt_dlp
                        ydl_opts = {'format': 'best', 'quiet': True}
                        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
                            ydl.download([url])
                        success = True
                    except:
                        # Try direct PDF download
                        success = downloader.download_pdf(url, output_file)
                
                # Send downloaded file
                if success and output_file and os.path.exists(output_file):
                    try:
                        # Determine file type and send accordingly
                        if output_file.endswith('.pdf'):
                            await message.reply_document(
                                document=output_file,
                                caption=f"✅ {title}"
                            )
                        else:
                            # Get file size
                            file_size = os.path.getsize(output_file)
                            
                            # Telegram's file size limit is 2GB
                            if file_size > 2 * 1024 * 1024 * 1024:
                                await message.reply_text(
                                    f"⚠️ {title}\n"
                                    f"File too large ({file_size / (1024**3):.2f}GB)\n"
                                    f"Telegram limit: 2GB"
                                )
                            else:
                                await message.reply_video(
                                    video=output_file,
                                    caption=f"✅ {title}",
                                    thumb=None
                                )
                        
                        download_count += 1
                        
                    except Exception as e:
                        await message.reply_text(f"❌ Failed to send {title}: {str(e)}")
                        error_count += 1
                    finally:
                        # Clean up
                        try:
                            os.remove(output_file)
                        except:
                            pass
                else:
                    await message.reply_text(f"❌ Failed to download: {title}")
                    error_count += 1
            
            except Exception as e:
                logger.error(f"Error processing line {line_num}: {e}")
                await message.reply_text(f"❌ Error: {str(e)[:100]}")
                error_count += 1
        
        # Final status
        await status_msg.edit_text(
            f"✅ **Download Complete!**\n\n"
            f"✅ Success: {download_count}\n"
            f"❌ Failed: {error_count}\n"
            f"📊 Total: {urls_found}"
        )
    
    except Exception as e:
        await status_msg.edit_text(f"❌ Error: {str(e)}")
        logger.error(f"Error in handle_document: {e}")
    
    finally:
        # Clean up
        if os.path.exists(txt_file_path):
            os.remove(txt_file_path)


@app.on_message(filters.text)
async def handle_text(client: Client, message: Message):
    """Handle text messages"""
    text = message.text.strip()
    
    if text.startswith('http'):
        # User sent a direct URL
        await message.reply_text(
            "💡 **Send as text file instead!**\n\n"
            "For better batch processing, create a `.txt` file with one URL per line and send it.\n\n"
            "Example:\n"
            "```\nTitle 1 : https://...\n"
            "Title 2 : https://...\n```"
        )
    else:
        await message.reply_text(
            "ℹ️ Send me a `.txt` file with URLs to download content!\n\n"
            "Use `/start` for more info."
        )


if __name__ == "__main__":
    logger.info("🤖 Content Downloader Bot Starting...")
    os.makedirs("downloads", exist_ok=True)
    
    try:
        app.run()
    except KeyboardInterrupt:
        logger.info("Bot stopped by user")
    except Exception as e:
        logger.error(f"Bot error: {e}")
