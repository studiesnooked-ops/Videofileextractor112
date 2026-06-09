import os
from flask import Flask

app = Flask(__name__)

@app.route('/')
def hello_world():
    return """
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Text-to-Video Bot</title>
    <style>
        body {
            font-family: Arial, sans-serif;
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            min-height: 100vh;
            display: flex;
            justify-content: center;
            align-items: center;
            margin: 0;
        }
        .container {
            background: white;
            border-radius: 10px;
            padding: 40px;
            box-shadow: 0 10px 25px rgba(0,0,0,0.2);
            text-align: center;
            max-width: 500px;
        }
        h1 {
            color: #667eea;
            margin: 0 0 20px 0;
        }
        .status {
            background: #d4edda;
            border: 1px solid #c3e6cb;
            color: #155724;
            padding: 15px;
            border-radius: 5px;
            margin: 20px 0;
        }
        .info {
            background: #e7f3ff;
            border: 1px solid #b3d9ff;
            color: #004085;
            padding: 15px;
            border-radius: 5px;
            margin: 20px 0;
            text-align: left;
        }
        .info p {
            margin: 8px 0;
            line-height: 1.6;
        }
        .footer {
            margin-top: 30px;
            color: #666;
            font-size: 12px;
        }
        .emoji {
            font-size: 48px;
            margin: 20px 0;
        }
    </style>
</head>
<body>
    <div class="container">
        <div class="emoji">🤖</div>
        <h1>Text-to-Video Bot</h1>
        
        <div class="status">
            <strong>✅ Bot is Running</strong>
        </div>
        
        <div class="info">
            <p><strong>How to use:</strong></p>
            <p>1. Add the bot on Telegram</p>
            <p>2. Send /start command</p>
            <p>3. Upload a .txt file with video URLs (one per line)</p>
            <p>4. The bot will download and send them to you</p>
        </div>
        
        <div class="footer">
            <p>Powered by Pyrogram & yt-dlp</p>
            <p>© 2024 - All rights reserved</p>
        </div>
    </div>
</body>
</html>
"""

@app.route('/health')
def health():
    """Health check endpoint for deployment platforms"""
    return {'status': 'healthy', 'service': 'text-to-video-bot'}, 200

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 8000))
    app.run(host="0.0.0.0", port=port, debug=False)
