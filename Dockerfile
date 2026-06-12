FROM python:3.12-slim

WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y \
    ffmpeg \
    && rm -rf /var/lib/apt/lists/*

# Install Python dependencies directly
RUN pip install --no-cache-dir \
    pyrogram \
    tgcrypto \
    yt-dlp \
    requests \
    flask \
    gunicorn

# Copy application code
COPY bot.py .

# Create downloads folder
RUN mkdir -p downloads

# Run both Flask and bot
CMD ["sh", "-c", "gunicorn bot:app --bind 0.0.0.0:$PORT & python3 bot.py"]
