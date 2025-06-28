FROM python:3.9-slim

WORKDIR /app

RUN apt-get update && apt-get -y install cron

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY . .

RUN chmod +x run.sh

RUN crontab crontab

COPY .env /app/.env

CMD ["cron", "-f"]
