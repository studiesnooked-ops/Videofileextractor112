FROM python:3.12-slim

WORKDIR /app

RUN apt-get update && apt-get install -y ffmpeg && rm -rf /var/lib/apt/lists/*

RUN pip install --no-cache-dir pyrogram tgcrypto yt-dlp requests flask gunicorn

COPY bot.py .

RUN mkdir -p downloads

CMD ["sh", "-c", "gunicorn bot:app --bind 0.0.0.0:$PORT & python3 bot.py"]
