FROM python:3.13-slim

WORKDIR /app

# Install tzdata and set timezone to Australia/Sydney
RUN apt-get update && apt-get install -y tzdata && \
    ln -sf /usr/share/zoneinfo/Australia/Sydney /etc/localtime && \
    echo "Australia/Sydney" > /etc/timezone && \
    dpkg-reconfigure -f noninteractive tzdata

RUN apt-get -y install cron

RUN mkdir -p /app/auth

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY . .
COPY servers /app/servers
COPY workers /app/workers

RUN chmod +x /app/run.sh

RUN crontab crontab

COPY .env /app/.env

COPY supervisord.conf .
CMD ["supervisord", "-c", "supervisord.conf"]
