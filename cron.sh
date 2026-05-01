#!/bin/bash

LOG_FILE="/home/ubuntu/job_scrapper/logs/cron_$(date +%Y-%m-%d).log"
mkdir -p /home/ubuntu/job_scrapper/logs

echo "======================================" >> "$LOG_FILE"
echo "Cron started: $(date)"                  >> "$LOG_FILE"
echo "======================================" >> "$LOG_FILE"

SCRAPERS=("trustme" "emploitic" "emploipartner" "algeriejob")
DIRS=("trustme_scraper" "emploitic_scraper" "emploipartner_scraper" "algeriejob_scraper")

for i in "${!SCRAPERS[@]}"; do
    SPIDER="${SCRAPERS[$i]}"
    DIR="${DIRS[$i]}"

    echo ""                                                        >> "$LOG_FILE"
    echo "[$(date +%H:%M:%S)] Starting $SPIDER..."                >> "$LOG_FILE"

    docker run --rm \
        --network job_network \
        job_scrapper \
        sh -c "cd /app/$DIR && scrapy crawl $SPIDER" >> "$LOG_FILE" 2>&1 \
        && echo "[$(date +%H:%M:%S)] ✅ $SPIDER done"   >> "$LOG_FILE" \
        || echo "[$(date +%H:%M:%S)] ❌ $SPIDER failed" >> "$LOG_FILE"
done

# ─── Deactivate expired jobs ───────────────────────────────────────────────────
echo ""                                                            >> "$LOG_FILE"
echo "[$(date +%H:%M:%S)] Deactivating expired jobs..."           >> "$LOG_FILE"

docker exec postgres_db psql -U admin -d job_scrapper -c \
    "SELECT deactivate_expired_jobs();" >> "$LOG_FILE" 2>&1 \
    && echo "[$(date +%H:%M:%S)] ✅ Expired jobs deactivated"  >> "$LOG_FILE" \
    || echo "[$(date +%H:%M:%S)] ❌ Deactivation failed"       >> "$LOG_FILE"

# ─── DB stats summary ─────────────────────────────────────────────────────────
echo ""                                                            >> "$LOG_FILE"
echo "[$(date +%H:%M:%S)] DB Stats:"                             >> "$LOG_FILE"

docker exec postgres_db psql -U admin -d job_scrapper -c \
    "SELECT name, last_crawl_at, execution_time,
            last_crawl_count, last_duplicate_count, total_jobs_count
     FROM sources;" >> "$LOG_FILE" 2>&1

docker exec postgres_db psql -U admin -d job_scrapper -c \
    "SELECT
        COUNT(*) FILTER (WHERE is_active = TRUE)  AS active_jobs,
        COUNT(*) FILTER (WHERE is_active = FALSE) AS inactive_jobs,
        COUNT(*)                                   AS total_jobs
     FROM jobs;" >> "$LOG_FILE" 2>&1

# ─── Delete log files older than 30 days ──────────────────────────────────────
find /home/ubuntu/job_scrapper/logs -name "cron_*.log" -mtime +30 -delete

echo ""                                                            >> "$LOG_FILE"
echo "======================================" >> "$LOG_FILE"
echo "Cron finished: $(date)"                 >> "$LOG_FILE"
echo "======================================" >> "$LOG_FILE"
