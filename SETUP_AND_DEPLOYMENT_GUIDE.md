# Setup & Deployment Guide - Text-to-Video Bot

## 📋 Prerequisites

You'll need:
1. **Telegram account** (obvious!)
2. **GitHub account** (for code hosting)
3. **Render account** (free deployment)
4. **API credentials** from Telegram:
   - `BOT_TOKEN` - Get from @BotFather on Telegram
   - `API_ID` - Get from https://my.telegram.org/auth/login
   - `API_HASH` - Get from https://my.telegram.org/auth/login

---

## 🔐 Step 1: Get Your Telegram Credentials

### Get BOT_TOKEN:
1. Open Telegram and search for `@BotFather`
2. Send `/start`
3. Send `/newbot`
4. Follow the prompts and copy your `BOT_TOKEN`

### Get API_ID & API_HASH:
1. Go to https://my.telegram.org
2. Log in with your phone number
3. Click "API Development Tools"
4. Create an app (fill in the form)
5. Copy `api_id` and `api_hash`

---

## 💻 Step 2: Set Up Locally (Test Before Deploying)

### Clone or set up your project:
```bash
# Create project directory
mkdir text-to-video-bot
cd text-to-video-bot

# Copy the FIXED files into this directory
# Replace the original files with the FIXED versions
```

### Create a `.env` file for local testing:
```bash
echo "API_ID=YOUR_API_ID
API_HASH=YOUR_API_HASH
BOT_TOKEN=YOUR_BOT_TOKEN" > .env
```

### Install dependencies locally:
```bash
python -m venv venv

# On Linux/Mac:
source venv/bin/activate

# On Windows:
venv\Scripts\activate

pip install -r requirements.txt
```

### Test the bot locally:
```bash
python main.py
```

You should see:
```
Bot is up and running...
```

---

## 🚀 Step 3: Deploy to Render

### 3.1 Push Code to GitHub:
```bash
git init
git add .
git commit -m "Initial commit"
git branch -M main
git remote add origin https://github.com/YOUR_USERNAME/text-to-video-bot.git
git push -u origin main
```

### 3.2 Deploy on Render:

1. Go to https://render.com
2. Sign up (or log in)
3. Click "New" → "Web Service"
4. Choose "Deploy existing repository"
5. Paste your GitHub repo URL
6. Fill in the settings:
   - **Name**: `text-to-video-bot`
   - **Environment**: `Docker`
   - **Branch**: `main`
7. Click "Advanced" and add environment variables:
   - `BOT_TOKEN` = your bot token
   - `API_ID` = your API ID
   - `API_HASH` = your API hash
8. Click "Create Web Service"

### 3.3 Monitor Deployment:
- Go to your Render dashboard
- Check logs in real-time
- Once "Build successful" appears, your bot is live!

---

## 🔄 Step 4: Verify Your Bot Works

1. Open Telegram
2. Search for your bot (the name you gave it to BotFather)
3. Send `/start` command
4. You should get a welcome message
5. Create a test file with URLs:
   ```
   https://www.youtube.com/watch?v=EXAMPLE1
   https://www.youtube.com/watch?v=EXAMPLE2
   ```
6. Send it to the bot and watch it download!

---

## 📝 Making Changes & Redeploying

After making code changes:

```bash
git add .
git commit -m "Description of changes"
git push origin main
```

Render will automatically redeploy your app.

---

## 🐛 Troubleshooting

### Bot doesn't respond?
- Check Render logs for errors
- Verify BOT_TOKEN is correct
- Ensure all env variables are set

### Videos don't download?
- Check that URLs are supported by yt-dlp
- Look for error messages in bot chat
- Check Render logs

### Free tier limitations?
- Render free tier has 750 hours/month
- Bot runs 24/7 = ~720 hours
- Consider upgrading if you need more uptime

---

## 📊 Project Structure (After Fixes)

```
text-to-video-bot/
├── app.py              ✅ FIXED - Flask web server
├── main.py             ✓ Bot logic (no changes needed)
├── vars.py             ✅ FIXED - Secure env handling
├── core.py             ✓ Helper functions
├── utils.py            ✓ Utility functions
├── p_bar.py            ✓ Progress bar
├── logs.py             ✓ Logging
├── requirements.txt    ✅ FIXED - All dependencies
├── Dockerfile          ✅ FIXED - Docker setup
├── render.yaml         ✅ FIXED - Render config
├── .gitignore          ✅ NEW - Ignore sensitive files
├── .env                (local only, not in git)
└── README.md           ✓ Documentation
```

---

## ✨ What Each FIXED File Changes

| File | Problem | Solution |
|------|---------|----------|
| `requirements.txt` | Missing flask, gunicorn | Added all dependencies |
| `vars.py` | Exposed API credentials | Removed defaults, proper validation |
| `app.py` | No port handling | Added PORT env var support |
| `Dockerfile` | Bad CMD syntax | Fixed multi-process execution |
| `render.yaml` | Wrong repo URL | Template for correct URL |
| `.gitignore` | Missing | Prevents committing secrets |

---

## 🎯 Checklist Before Deploying

- [ ] All FIXED files are in place
- [ ] BOT_TOKEN works (tested with @BotFather)
- [ ] API_ID and API_HASH are correct
- [ ] `.env` file created and in `.gitignore`
- [ ] Code pushed to GitHub
- [ ] Environment variables set in Render
- [ ] Bot responds to `/start` command
- [ ] Test download works with a real URL

---

## 📞 Support Resources

- **Pyrogram Docs**: https://docs.pyrogram.org
- **yt-dlp Guide**: https://github.com/yt-dlp/yt-dlp
- **Render Docs**: https://render.com/docs
- **Telegram Bot API**: https://core.telegram.org/bots/api

---

## 🎉 You're Done!

Your bot is now live and ready to download videos! 🚀

Questions? Check the logs in Render or test locally first.
