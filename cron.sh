#!/bin/bash

LOG_FILE="/home/ubuntu/job_scrapper/logs/cron_$(date +%Y-%m-%d).log"
mkdir -p /home/ubuntu/job_scrapper/logs

echo "======================================" >> "$LOG_FILE"
echo "Cron started: $(date)" >> "$LOG_FILE"
echo "======================================" >> "$LOG_FILE"

SCRAPERS=("trustme" "emploitic" "emploipartner" "algeriejob")
DIRS=("trustme_scraper" "emploitic_scraper" "emploipartner_scraper" "algeriejob_scraper")

for i in "${!SCRAPERS[@]}"; do
    SPIDER="${SCRAPERS[$i]}"
    DIR="${DIRS[$i]}"
    echo "" >> "$LOG_FILE"
    echo "[$(date +%H:%M:%S)] Starting $SPIDER..." >> "$LOG_FILE"

    docker run --rm \
        --network job_network \
        job_scrapper \
        sh -c "cd /app/$DIR && scrapy crawl $SPIDER" >> "$LOG_FILE" 2>&1 \
        && echo "[$(date +%H:%M:%S)] ✅ $SPIDER done" >> "$LOG_FILE" \
        || echo "[$(date +%H:%M:%S)] ❌ $SPIDER failed" >> "$LOG_FILE"
done

echo "" >> "$LOG_FILE"
echo "Cron finished: $(date)" >> "$LOG_FILE"
