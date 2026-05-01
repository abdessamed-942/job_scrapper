#!/bin/bash

LOG_FILE="/home/ubuntu/job_scrapper/logs/telegram_$(date +%Y-%m-%d).log"
mkdir -p /home/ubuntu/job_scrapper/logs

echo ""                                                              >> "$LOG_FILE"
echo "[$(date +%H:%M:%S)] Sending new jobs to Telegram..."          >> "$LOG_FILE"

/home/ubuntu/job_scrapper/venv/bin/python3 \
    /home/ubuntu/job_scrapper/telegram_sender.py >> "$LOG_FILE" 2>&1 \
    && echo "[$(date +%H:%M:%S)] ✅ Telegram done"   >> "$LOG_FILE" \
    || echo "[$(date +%H:%M:%S)] ❌ Telegram failed" >> "$LOG_FILE"
