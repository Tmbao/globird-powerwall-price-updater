FROM python:3.13-slim

WORKDIR /app

ARG LXC_INIT_MODE=services
ENV LXC_INIT_MODE=${LXC_INIT_MODE}
ENV PYTHONUNBUFFERED=1

# Install tzdata and set timezone to Australia/Sydney
RUN apt-get update && apt-get install -y tzdata cron && \
    ln -sf /usr/share/zoneinfo/Australia/Sydney /etc/localtime && \
    echo "Australia/Sydney" > /etc/timezone && \
    dpkg-reconfigure -f noninteractive tzdata && \
    rm -rf /var/lib/apt/lists/*

RUN mkdir -p /app/auth /var/log

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY . .
COPY servers /app/servers
COPY workers /app/workers
COPY lxc-init.sh /sbin/init
COPY lxc-services.sh /app/lxc-services.sh

RUN chmod +x /app/run.sh /app/lxc-services.sh /sbin/init

RUN crontab crontab

COPY .env /app/.env
RUN sed -i 's/\r$//' /app/run.sh /app/lxc-services.sh /sbin/init /app/crontab /app/.env

CMD ["/sbin/init"]
