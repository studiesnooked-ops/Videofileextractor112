"""
Enhanced Telegram Bot with ClassX Support
Downloads from YouTube, Instagram, TikTok, and ClassX courses
"""

import os
import re
import yt_dlp
import asyncio
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

print(f"📁 Downloads directory: {os.path.abspath(DOWNLOADS_DIR)}")


class URLProcessor:
    """Process different types of URLs"""
    
    @staticmethod
    def is_classx_url(url):
        """Check if URL is from ClassX"""
        classx_domains = ['appxapi.vercel.app', 'classx.co.in', 'clsx.media', 'classx']
        return any(domain in url.lower() for domain in classx_domains)
    
    @staticmethod
    def is_video_url(url):
        """Check if URL is a video platform"""
        video_domains = [
            'youtube.com', 'youtu.be',
            'instagram.com', 'tiktok.com',
            'facebook.com', 'fb.watch',
            'twitter.com', 'x.com',
            'dailymotion.com', 'vimeo.com',
            'sharechat.com', ' Moj'
        ]
        return any(domain in url.lower() for domain in video_domains)
    
    @staticmethod
    def is_m3u8_url(url):
        """Check if URL is m3u8 stream"""
        return '.m3u8' in url.lower()
    
    @staticmethod
    def is_pdf_url(url):
        """Check if URL is PDF"""
        return url.lower().endswith('.pdf') or '/pdf' in url.lower()
    
    @staticmethod
    def extract_video_id(url):
        """Extract video ID for better processing"""
        # YouTube
        yt_match = re.search(r'(?:v=|/v/|youtu\.be/)([a-zA-Z0-9_-]{11})', url)
        if yt_match:
            return ('youtube', yt_match.group(1))
        
        # TikTok
        tt_match = re.search(r'tiktok\.com/@[\w]+/video/(\d+)', url)
        if tt_match:
            return ('tiktok', tt_match.group(1))
        
        return ('unknown', None)


class Downloader:
    """Download media from various sources"""
    
    @staticmethod
    def download_video_ytdlp(url, title, message):
        """Download video using yt-dlp"""
        try:
            print(f"[DEBUG] Downloading video: {title}")
            print(f"[DEBUG] URL: {url}")
            
            # Clean title for filename
            safe_title = re.sub(r'[^\w\s-]', '', title).strip()[:50]
            safe_title = safe_title.replace(' ', '_')
            
            output_path = os.path.join(DOWNLOADS_DIR, f"{safe_title}.mp4")
            
            ydl_opts = {
                'format': 'bestvideo[ext=mp4]+bestaudio[ext=m4a]/best[ext=mp4]/best',
                'outtmpl': output_path,
                'quiet': False,
                'no_warnings': False,
                'extract_flat': False,
                'socket_timeout': 30,
            }
            
            with yt_dlp.YoutubeDL(ydl_opts) as ydl:
                # Get video info first
                try:
                    info = ydl.extract_info(url, download=False)
                    if not info:
                        print("[ERROR] Could not extract video info")
                        return None
                    
                    print(f"[DEBUG] Video title: {info.get('title', 'Unknown')}")
                    print(f"[DEBUG] Duration: {info.get('duration', 0)} seconds")
                    
                    # Now download
                    ydl.download(url)
                except Exception as e:
                    print(f"[ERROR] Extract info failed: {e}")
                    # Try direct download
                    ydl.download(url)
            
            # Check if file exists
            if os.path.exists(output_path):
                print(f"[DEBUG] File downloaded: {output_path}")
                return output_path
            
            # Try to find any downloaded file
            files = os.listdir(DOWNLOADS_DIR)
            for f in files:
                if safe_title.replace('_', '') in f.replace('_', ''):
                    full_path = os.path.join(DOWNLOADS_DIR, f)
                    if os.path.isfile(full_path):
                        print(f"[DEBUG] Found file: {full_path}")
                        return full_path
            
            print("[ERROR] No file found after download")
            return None
        
        except Exception as e:
            print(f"[ERROR] yt-dlp error: {e}")
            import traceback
            traceback.print_exc()
            return None
    
    @staticmethod
    def download_m3u8(m3u8_url, title):
        """Download m3u8 stream using ffmpeg"""
        try:
            print(f"[DEBUG] Downloading m3u8: {title}")
            print(f"[DEBUG] URL: {m3u8_url}")
            
            safe_title = re.sub(r'[^\w\s-]', '', title).strip()[:50]
            safe_title = safe_title.replace(' ', '_')
            
            output_path = os.path.join(DOWNLOADS_DIR, f"{safe_title}.mp4")
            
            # Check if ffmpeg exists
            ffmpeg_path = None
            for path in ['ffmpeg', '/usr/bin/ffmpeg', '/usr/local/bin/ffmpeg']:
                try:
                    subprocess.run([path, '-version'], capture_output=True, timeout=5)
                    ffmpeg_path = path
                    break
                except:
                    continue
            
            if not ffmpeg_path:
                print("[ERROR] ffmpeg not found")
                return None
            
            cmd = [
                ffmpeg_path,
                '-i', m3u8_url,
                '-c', 'copy',
                '-bsf:a', 'aac_adtstoasc',
                '-y',
                '-timeout', '600000000',
                output_path
            ]
            
            print(f"[DEBUG] Running ffmpeg command...")
            result = subprocess.run(
                cmd, 
                capture_output=True, 
                timeout=600,
                text=True
            )
            
            print(f"[DEBUG] ffmpeg return code: {result.returncode}")
            if result.returncode != 0:
                print(f"[DEBUG] ffmpeg stderr: {result.stderr[:500]}")
            
            if os.path.exists(output_path):
                print(f"[DEBUG] File downloaded: {output_path}")
                return output_path
            
            return None
        
        except subprocess.TimeoutExpired:
            print("[ERROR] ffmpeg timeout")
            return None
        except Exception as e:
            print(f"[ERROR] ffmpeg error: {e}")
            import traceback
            traceback.print_exc()
            return None
    
    @staticmethod
    def download_file(url, title):
        """Download generic file (PDF, etc)"""
        try:
            print(f"[DEBUG] Downloading file: {title}")
            print(f"[DEBUG] URL: {url}")
            
            safe_title = re.sub(r'[^\w\s-]', '', title).strip()[:50]
            safe_title = safe_title.replace(' ', '_')
            
            # Determine extension
            ext = '.mp4'
            if url.lower().endswith('.pdf'):
                ext = '.pdf'
            
            output_path = os.path.join(DOWNLOADS_DIR, f"{safe_title}{ext}")
            
            response = requests.get(url, timeout=60, stream=True)
            
            if response.status_code == 200:
                with open(output_path, 'wb') as f:
                    for chunk in response.iter_content(chunk_size=8192):
                        if chunk:
                            f.write(chunk)
                
                if os.path.exists(output_path):
                    print(f"[DEBUG] File downloaded: {output_path}")
                    return output_path
            
            print(f"[ERROR] HTTP {response.status_code}")
            return None
        
        except Exception as e:
            print(f"[ERROR] Download error: {e}")
            return None


class ClassXDownloader:
    """Handle ClassX API downloads"""
    
    @staticmethod
    def get_stream_url(api_url):
        """Extract stream URL from ClassX API response"""
        try:
            print(f"[DEBUG] Getting stream URL from: {api_url}")
            
            response = requests.get(api_url, timeout=15)
            
            if response.status_code != 200:
                print(f"[ERROR] API returned {response.status_code}")
                return None
            
            try:
                data = response.json()
                print(f"[DEBUG] API Response: {str(data)[:200]}")
                
                # Try common keys
                keys_to_try = [
                    'url', 'video_url', 'm3u8', 'stream_url', 
                    'playUrl', 'downloadUrl', 'link', 'videoLink',
                    'media_url', 'source'
                ]
                
                for key in keys_to_try:
                    if key in data and data[key]:
                        url = data[key]
                        if isinstance(url, str) and 'http' in url:
                            print(f"[DEBUG] Found URL in key '{key}'")
                            return url
                
                # Search for URL in nested data
                found_url = ClassXDownloader._find_url_recursive(data)
                if found_url:
                    return found_url
                
            except ValueError:
                # Not JSON, check if it's the URL itself
                text = response.text
                if 'http' in text and '.m3u8' in text:
                    # Find the m3u8 URL
                    match = re.search(r'https?://[^\s"\']+\.m3u8[^\s"\']*', text)
                    if match:
                        return match.group(0)
                elif text.startswith('http'):
                    return text.strip()
            
            return None
        
        except Exception as e:
            print(f"[ERROR] API error: {e}")
            return None
    
    @staticmethod
    def _find_url_recursive(data, depth=0):
        """Recursively find URL in nested dict"""
        if depth > 10:
            return None
        
        if isinstance(data, dict):
            for key, value in data.items():
                if 'url' in key.lower() or 'link' in key.lower():
                    if isinstance(value, str) and value.startswith('http'):
                        return value
                if isinstance(value, (dict, list)):
                    result = ClassXDownloader._find_url_recursive(value, depth + 1)
                    if result:
                        return result
        
        elif isinstance(data, list):
            for item in data:
                if isinstance(item, (dict, list)):
                    result = ClassXDownloader._find_url_recursive(item, depth + 1)
                    if result:
                        return result
        
        return None


# Bot Commands
@app.on_message(filters.command("start"))
async def start_command(client, message):
    """Start command"""
    await message.reply_text(
        "🤖 **Media Downloader Bot**\n\n"
        "Send me a `.txt` file with links.\n\n"
        "**Format:** `Title : URL`\n"
        "One link per line\n\n"
        "**Supported:**\n"
        "• YouTube, Instagram, TikTok\n"
        "• ClassX courses (m3u8/PDF)\n"
        "• Other video platforms"
    )


@app.on_message(filters.command("test"))
async def test_command(client, message):
    """Test command to check bot status"""
    await message.reply_text(
        f"✅ Bot is running!\n"
        f"📁 Download dir: {DOWNLOADS_DIR}\n"
        f"📂 Files: {len(os.listdir(DOWNLOADS_DIR))}"
    )


@app.on_message(filters.document)
async def handle_document(client, message):
    """Handle .txt file uploads"""
    
    if message.document.mime_type not in ['text/plain', 'application/octet-stream']:
        await message.reply_text("❌ Please send a .txt file only")
        return
    
    txt_file_path = None
    
    try:
        # Download the file
        status_msg = await message.reply_text("📥 Downloading file...")
        
        txt_file_path = await message.download()
        print(f"[DEBUG] File downloaded to: {txt_file_path}")
        
        # Read lines
        with open(txt_file_path, 'r', encoding='utf-8') as f:
            lines = f.readlines()
        
        # Parse lines
        tasks = []
        for line in lines:
            line = line.strip()
            if not line or ':' not in line:
                continue
            
            parts = line.split(':', 1)
            if len(parts) != 2:
                continue
            
            title = parts[0].strip()
            url = parts[1].strip()
            
            if not url.startswith('http'):
                continue
            
            tasks.append((title, url))
        
        if not tasks:
            await status_msg.edit_text("❌ No valid links found in file")
            return
        
        await status_msg.edit_text(
            f"📋 Found {len(tasks)} links\n"
            f"Starting download..."
        )
        
        # Process each task
        success_count = 0
        fail_count = 0
        
        for idx, (title, url) in enumerate(tasks, 1):
            await status_msg.edit_text(
                f"⬇️ [{idx}/{len(tasks)}] Downloading:\n"
                f"{title}"
            )
            
            print(f"\n{'='*50}")
            print(f"Processing: {title}")
            print(f"URL: {url}")
            print(f"{'='*50}")
            
            downloaded_file = None
            
            # Determine download method
            try:
                if URLProcessor.is_classx_url(url):
                    print("[DEBUG] ClassX URL detected")
                    
                    if URLProcessor.is_m3u8_url(url) or 'main.m3u8' in url:
                        # Direct m3u8 URL
                        stream_url = ClassXDownloader.get_stream_url(url)
                        if stream_url:
                            downloaded_file = Downloader.download_m3u8(stream_url, title)
                        else:
                            # Try as is
                            downloaded_file = Downloader.download_m3u8(url, title)
                    
                    elif URLProcessor.is_pdf_url(url):
                        downloaded_file = Downloader.download_file(url, title)
                    
                    else:
                        # Try to get stream from API
                        stream_url = ClassXDownloader.get_stream_url(url)
                        if stream_url:
                            if '.m3u8' in stream_url:
                                downloaded_file = Downloader.download_m3u8(stream_url, title)
                            else:
                                downloaded_file = Downloader.download_file(stream_url, title)
                        else:
                            # Try direct download
                            downloaded_file = Downloader.download_file(url, title)
                
                elif URLProcessor.is_m3u8_url(url):
                    print("[DEBUG] m3u8 URL detected")
                    downloaded_file = Downloader.download_m3u8(url, title)
                
                elif URLProcessor.is_pdf_url(url):
                    print("[DEBUG] PDF URL detected")
                    downloaded_file = Downloader.download_file(url, title)
                
                elif URLProcessor.is_video_url(url):
                    print("[DEBUG] Video URL detected")
                    downloaded_file = Downloader.download_video_ytdlp(url, title, message)
                
                else:
                    print("[DEBUG] Unknown URL, trying generic download")
                    # Try yt-dlp first
                    downloaded_file = Downloader.download_video_ytdlp(url, title, message)
                    if not downloaded_file:
                        # Try as direct file
                        downloaded_file = Downloader.download_file(url, title)
                
                # Send the file
                if downloaded_file and os.path.exists(downloaded_file):
                    file_size = os.path.getsize(downloaded_file)
                    print(f"[DEBUG] Sending file: {downloaded_file} ({file_size} bytes)")
                    
                    try:
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
                        success_count += 1
                        
                        # Cleanup
                        try:
                            os.remove(downloaded_file)
                            print(f"[DEBUG] Cleaned up: {downloaded_file}")
                        except:
                            pass
                    
                    except Exception as e:
                        print(f"[ERROR] Send error: {e}")
                        fail_count += 1
                else:
                    print(f"[ERROR] Download failed for: {title}")
                    await message.reply_text(f"❌ Failed: {title}")
                    fail_count += 1
                    
            except Exception as e:
                print(f"[ERROR] Processing error: {e}")
                import traceback
                traceback.print_exc()
                await message.reply_text(f"❌ Error: {title}")
                fail_count += 1
        
        # Final status
        await status_msg.edit_text(
            f"✅ Completed!\n"
            f"Success: {success_count}\n"
            f"Failed: {fail_count}"
        )
    
    except Exception as e:
        print(f"[ERROR] Main error: {e}")
        import traceback
        traceback.print_exc()
        await message.reply_text(f"❌ Error: {str(e)[:200]}")
    
    finally:
        # Cleanup
        if txt_file_path and os.path.exists(txt_file_path):
            try:
                os.remove(txt_file_path)
                print(f"[DEBUG] Cleaned up txt: {txt_file_path}")
            except:
                pass


if __name__ == "__main__":
    print("🤖 Starting bot...")
    print(f"📁 Downloads folder: {os.path.abspath(DOWNLOADS_DIR)}")
    
    # List contents
    if os.path.exists(DOWNLOADS_DIR):
        files = os.listdir(DOWNLOADS_DIR)
        print(f"📂 Current files:"""
Enhanced Telegram Bot with ClassX Support
Downloads from YouTube, Instagram, TikTok, and ClassX courses
"""

import os
import re
import yt_dlp
import asyncio
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

print(f"📁 Downloads directory: {os.path.abspath(DOWNLOADS_DIR)}")


class URLProcessor:
    """Process different types of URLs"""
    
    @staticmethod
    def is_classx_url(url):
        """Check if URL is from ClassX"""
        classx_domains = ['appxapi.vercel.app', 'classx.co.in', 'clsx.media', 'classx']
        return any(domain in url.lower() for domain in classx_domains)
    
    @staticmethod
    def is_video_url(url):
        """Check if URL is a video platform"""
        video_domains = [
            'youtube.com', 'youtu.be',
            'instagram.com', 'tiktok.com',
            'facebook.com', 'fb.watch',
            'twitter.com', 'x.com',
            'dailymotion.com', 'vimeo.com',
            'sharechat.com', ' Moj'
        ]
        return any(domain in url.lower() for domain in video_domains)
    
    @staticmethod
    def is_m3u8_url(url):
        """Check if URL is m3u8 stream"""
        return '.m3u8' in url.lower()
    
    @staticmethod
    def is_pdf_url(url):
        """Check if URL is PDF"""
        return url.lower().endswith('.pdf') or '/pdf' in url.lower()
    
    @staticmethod
    def extract_video_id(url):
        """Extract video ID for better processing"""
        # YouTube
        yt_match = re.search(r'(?:v=|/v/|youtu\.be/)([a-zA-Z0-9_-]{11})', url)
        if yt_match:
            return ('youtube', yt_match.group(1))
        
        # TikTok
        tt_match = re.search(r'tiktok\.com/@[\w]+/video/(\d+)', url)
        if tt_match:
            return ('tiktok', tt_match.group(1))
        
        return ('unknown', None)


class Downloader:
    """Download media from various sources"""
    
    @staticmethod
    def download_video_ytdlp(url, title, message):
        """Download video using yt-dlp"""
        try:
            print(f"[DEBUG] Downloading video: {title}")
            print(f"[DEBUG] URL: {url}")
            
            # Clean title for filename
            safe_title = re.sub(r'[^\w\s-]', '', title).strip()[:50]
            safe_title = safe_title.replace(' ', '_')
            
            output_path = os.path.join(DOWNLOADS_DIR, f"{safe_title}.mp4")
            
            ydl_opts = {
                'format': 'bestvideo[ext=mp4]+bestaudio[ext=m4a]/best[ext=mp4]/best',
                'outtmpl': output_path,
                'quiet': False,
                'no_warnings': False,
                'extract_flat': False,
                'socket_timeout': 30,
            }
            
            with yt_dlp.YoutubeDL(ydl_opts) as ydl:
                # Get video info first
                try:
                    info = ydl.extract_info(url, download=False)
                    if not info:
                        print("[ERROR] Could not extract video info")
                        return None
                    
                    print(f"[DEBUG] Video title: {info.get('title', 'Unknown')}")
                    print(f"[DEBUG] Duration: {info.get('duration', 0)} seconds")
                    
                    # Now download
                    ydl.download(url)
                except Exception as e:
                    print(f"[ERROR] Extract info failed: {e}")
                    # Try direct download
                    ydl.download(url)
            
            # Check if file exists
            if os.path.exists(output_path):
                print(f"[DEBUG] File downloaded: {output_path}")
                return output_path
            
            # Try to find any downloaded file
            files = os.listdir(DOWNLOADS_DIR)
            for f in files:
                if safe_title.replace('_', '') in f.replace('_', ''):
                    full_path = os.path.join(DOWNLOADS_DIR, f)
                    if os.path.isfile(full_path):
                        print(f"[DEBUG] Found file: {full_path}")
                        return full_path
            
            print("[ERROR] No file found after download")
            return None
        
        except Exception as e:
            print(f"[ERROR] yt-dlp error: {e}")
            import traceback
            traceback.print_exc()
            return None
    
    @staticmethod
    def download_m3u8(m3u8_url, title):
        """Download m3u8 stream using ffmpeg"""
        try:
            print(f"[DEBUG] Downloading m3u8: {title}")
            print(f"[DEBUG] URL: {m3u8_url}")
            
            safe_title = re.sub(r'[^\w\s-]', '', title).strip()[:50]
            safe_title = safe_title.replace(' ', '_')
            
            output_path = os.path.join(DOWNLOADS_DIR, f"{safe_title}.mp4")
            
            # Check if ffmpeg exists
            ffmpeg_path = None
            for path in ['ffmpeg', '/usr/bin/ffmpeg', '/usr/local/bin/ffmpeg']:
                try:
                    subprocess.run([path, '-version'], capture_output=True, timeout=5)
                    ffmpeg_path = path
                    break
                except:
                    continue
            
            if not ffmpeg_path:
                print("[ERROR] ffmpeg not found")
                return None
            
            cmd = [
                ffmpeg_path,
                '-i', m3u8_url,
                '-c', 'copy',
                '-bsf:a', 'aac_adtstoasc',
                '-y',
                '-timeout', '600000000',
                output_path
            ]
            
            print(f"[DEBUG] Running ffmpeg command...")
            result = subprocess.run(
                cmd, 
                capture_output=True, 
                timeout=600,
                text=True
            )
            
            print(f"[DEBUG] ffmpeg return code: {result.returncode}")
            if result.returncode != 0:
                print(f"[DEBUG] ffmpeg stderr: {result.stderr[:500]}")
            
            if os.path.exists(output_path):
                print(f"[DEBUG] File downloaded: {output_path}")
                return output_path
            
            return None
        
        except subprocess.TimeoutExpired:
            print("[ERROR] ffmpeg timeout")
            return None
        except Exception as e:
            print(f"[ERROR] ffmpeg error: {e}")
            import traceback
            traceback.print_exc()
            return None
    
    @staticmethod
    def download_file(url, title):
        """Download generic file (PDF, etc)"""
        try:
            print(f"[DEBUG] Downloading file: {title}")
            print(f"[DEBUG] URL: {url}")
            
            safe_title = re.sub(r'[^\w\s-]', '', title).strip()[:50]
            safe_title = safe_title.replace(' ', '_')
            
            # Determine extension
            ext = '.mp4'
            if url.lower().endswith('.pdf'):
                ext = '.pdf'
            
            output_path = os.path.join(DOWNLOADS_DIR, f"{safe_title}{ext}")
            
            response = requests.get(url, timeout=60, stream=True)
            
            if response.status_code == 200:
                with open(output_path, 'wb') as f:
                    for chunk in response.iter_content(chunk_size=8192):
                        if chunk:
                            f.write(chunk)
                
                if os.path.exists(output_path):
                    print(f"[DEBUG] File downloaded: {output_path}")
                    return output_path
            
            print(f"[ERROR] HTTP {response.status_code}")
            return None
        
        except Exception as e:
            print(f"[ERROR] Download error: {e}")
            return None


class ClassXDownloader:
    """Handle ClassX API downloads"""
    
    @staticmethod
    def get_stream_url(api_url):
        """Extract stream URL from ClassX API response"""
        try:
            print(f"[DEBUG] Getting stream URL from: {api_url}")
            
            response = requests.get(api_url, timeout=15)
            
            if response.status_code != 200:
                print(f"[ERROR] API returned {response.status_code}")
                return None
            
            try:
                data = response.json()
                print(f"[DEBUG] API Response: {str(data)[:200]}")
                
                # Try common keys
                keys_to_try = [
                    'url', 'video_url', 'm3u8', 'stream_url', 
                    'playUrl', 'downloadUrl', 'link', 'videoLink',
                    'media_url', 'source'
                ]
                
                for key in keys_to_try:
                    if key in data and data[key]:
                        url = data[key]
                        if isinstance(url, str) and 'http' in url:
                            print(f"[DEBUG] Found URL in key '{key}'")
                            return url
                
                # Search for URL in nested data
                found_url = ClassXDownloader._find_url_recursive(data)
                if found_url:
                    return found_url
                
            except ValueError:
                # Not JSON, check if it's the URL itself
                text = response.text
                if 'http' in text and '.m3u8' in text:
                    # Find the m3u8 URL
                    match = re.search(r'https?://[^\s"\']+\.m3u8[^\s"\']*', text)
                    if match:
                        return match.group(0)
                elif text.startswith('http'):
                    return text.strip()
            
            return None
        
        except Exception as e:
            print(f"[ERROR] API error: {e}")
            return None
    
    @staticmethod
    def _find_url_recursive(data, depth=0):
        """Recursively find URL in nested dict"""
        if depth > 10:
            return None
        
        if isinstance(data, dict):
            for key, value in data.items():
                if 'url' in key.lower() or 'link' in key.lower():
                    if isinstance(value, str) and value.startswith('http'):
                        return value
                if isinstance(value, (dict, list)):
                    result = ClassXDownloader._find_url_recursive(value, depth + 1)
                    if result:
                        return result
        
        elif isinstance(data, list):
            for item in data:
                if isinstance(item, (dict, list)):
                    result = ClassXDownloader._find_url_recursive(item, depth + 1)
                    if result:
                        return result
        
        return None


# Bot Commands
@app.on_message(filters.command("start"))
async def start_command(client, message):
    """Start command"""
    await message.reply_text(
        "🤖 **Media Downloader Bot**\n\n"
        "Send me a `.txt` file with links.\n\n"
        "**Format:** `Title : URL`\n"
        "One link per line\n\n"
        "**Supported:**\n"
        "• YouTube, Instagram, TikTok\n"
        "• ClassX courses (m3u8/PDF)\n"
        "• Other video platforms"
    )


@app.on_message(filters.command("test"))
async def test_command(client, message):
    """Test command to check bot status"""
    await message.reply_text(
        f"✅ Bot is running!\n"
        f"📁 Download dir: {DOWNLOADS_DIR}\n"
        f"📂 Files: {len(os.listdir(DOWNLOADS_DIR))}"
    )


@app.on_message(filters.document)
async def handle_document(client, message):
    """Handle .txt file uploads"""
    
    if message.document.mime_type not in ['text/plain', 'application/octet-stream']:
        await message.reply_text("❌ Please send a .txt file only")
        return
    
    txt_file_path = None
    
    try:
        # Download the file
        status_msg = await message.reply_text("📥 Downloading file...")
        
        txt_file_path = await message.download()
        print(f"[DEBUG] File downloaded to: {txt_file_path}")
        
        # Read lines
        with open(txt_file_path, 'r', encoding='utf-8') as f:
            lines = f.readlines()
        
        # Parse lines
        tasks = []
        for line in lines:
            line = line.strip()
            if not line or ':' not in line:
                continue
            
            parts = line.split(':', 1)
            if len(parts) != 2:
                continue
            
            title = parts[0].strip()
            url = parts[1].strip()
            
            if not url.startswith('http'):
                continue
            
            tasks.append((title, url))
        
        if not tasks:
            await status_msg.edit_text("❌ No valid links found in file")
            return
        
        await status_msg.edit_text(
            f"📋 Found {len(tasks)} links\n"
            f"Starting download..."
        )
        
        # Process each task
        success_count = 0
        fail_count = 0
        
        for idx, (title, url) in enumerate(tasks, 1):
            await status_msg.edit_text(
                f"⬇️ [{idx}/{len(tasks)}] Downloading:\n"
                f"{title}"
            )
            
            print(f"\n{'='*50}")
            print(f"Processing: {title}")
            print(f"URL: {url}")
            print(f"{'='*50}")
            
            downloaded_file = None
            
            # Determine download method
            try:
                if URLProcessor.is_classx_url(url):
                    print("[DEBUG] ClassX URL detected")
                    
                    if URLProcessor.is_m3u8_url(url) or 'main.m3u8' in url:
                        # Direct m3u8 URL
                        stream_url = ClassXDownloader.get_stream_url(url)
                        if stream_url:
                            downloaded_file = Downloader.download_m3u8(stream_url, title)
                        else:
                            # Try as is
                            downloaded_file = Downloader.download_m3u8(url, title)
                    
                    elif URLProcessor.is_pdf_url(url):
                        downloaded_file = Downloader.download_file(url, title)
                    
                    else:
                        # Try to get stream from API
                        stream_url = ClassXDownloader.get_stream_url(url)
                        if stream_url:
                            if '.m3u8' in stream_url:
                                downloaded_file = Downloader.download_m3u8(stream_url, title)
                            else:
                                downloaded_file = Downloader.download_file(stream_url, title)
                        else:
                            # Try direct download
                            downloaded_file = Downloader.download_file(url, title)
                
                elif URLProcessor.is_m3u8_url(url):
                    print("[DEBUG] m3u8 URL detected")
                    downloaded_file = Downloader.download_m3u8(url, title)
                
                elif URLProcessor.is_pdf_url(url):
                    print("[DEBUG] PDF URL detected")
                    downloaded_file = Downloader.download_file(url, title)
                
                elif URLProcessor.is_video_url(url):
                    print("[DEBUG] Video URL detected")
                    downloaded_file = Downloader.download_video_ytdlp(url, title, message)
                
                else:
                    print("[DEBUG] Unknown URL, trying generic download")
                    # Try yt-dlp first
                    downloaded_file = Downloader.download_video_ytdlp(url, title, message)
                    if not downloaded_file:
                        # Try as direct file
                        downloaded_file = Downloader.download_file(url, title)
                
                # Send the file
                if downloaded_file and os.path.exists(downloaded_file):
                    file_size = os.path.getsize(downloaded_file)
                    print(f"[DEBUG] Sending file: {downloaded_file} ({file_size} bytes)")
                    
                    try:
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
                        success_count += 1
                        
                        # Cleanup
                        try:
                            os.remove(downloaded_file)
                            print(f"[DEBUG] Cleaned up: {downloaded_file}")
                        except:
                            pass
                    
                    except Exception as e:
                        print(f"[ERROR] Send error: {e}")
                        fail_count += 1
                else:
                    print(f"[ERROR] Download failed for: {title}")
                    await message.reply_text(f"❌ Failed: {title}")
                    fail_count += 1
                    
            except Exception as e:
                print(f"[ERROR] Processing error: {e}")
                import traceback
                traceback.print_exc()
                await message.reply_text(f"❌ Error: {title}")
                fail_count += 1
        
        # Final status
        await status_msg.edit_text(
            f"✅ Completed!\n"
            f"Success: {success_count}\n"
            f"Failed: {fail_count}"
        )
    
    except Exception as e:
        print(f"[ERROR] Main error: {e}")
        import traceback
        traceback.print_exc()
        await message.reply_text(f"❌ Error: {str(e)[:200]}")
    
    finally:
        # Cleanup
        if txt_file_path and os.path.exists(txt_file_path):
            try:
                os.remove(txt_file_path)
                print(f"[DEBUG] Cleaned up txt: {txt_file_path}")
            except:
                pass


if __name__ == "__main__":
    print("🤖 Starting bot...")
    print(f"📁 Downloads folder: {os.path.abspath(DOWNLOADS_DIR)}")
    
    # List contents
    if os.path.exists(DOWNLOADS_DIR):
        files = os.listdir(DOWNLOADS_DIR)
        print(f"📂 Current files:
