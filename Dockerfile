FROM python:3.12-slim

WORKDIR /app

# Install system dependencies (including gcc for tgcrypto)
RUN apt-get update && apt-get install -y \
    ffmpeg \
    gcc \
    python3-dev \
    && rm -rf /var/lib/apt/lists/*

# Install Python dependencies
RUN pip install --no-cache-dir pyrogram tgcrypto yt-dlp requests flask gunicorn

COPY bot.py .

RUN mkdir -p downloads

CMD ["sh", "-c", "gunicorn bot:app --bind 0.0.0.0:$PORT & python3 bot.py"]
