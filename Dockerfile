FROM python:3.13-slim

WORKDIR /app

RUN apt-get update && apt-get -y install cron

RUN mkdir -p /app/auth

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY . .
COPY servers /app/servers
COPY workers /app/workers

RUN chmod +x run.sh

RUN crontab crontab

COPY .env /app/.env

COPY supervisord.conf .
CMD ["supervisord", "-c", "supervisord.conf"]
