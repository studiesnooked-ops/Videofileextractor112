FROM python:3.12-slim

RUN apt-get update && apt-get install -y \
    ffmpeg \
    supervisor \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /app

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY . .
COPY supervisord.conf /etc/supervisord.conf

RUN mkdir -p downloads

CMD ["/usr/bin/supervisord", "-c", "/etc/supervisord.conf"]
