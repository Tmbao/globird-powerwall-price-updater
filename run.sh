#!/usr/bin/bash
source /app/.env
/usr/local/bin/python /app/workers/price_updater.py
