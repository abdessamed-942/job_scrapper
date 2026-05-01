#!/bin/bash

set -e

TIMESTAMP=$(date +"%Y-%m-%d_%H-%M-%S")
OUTPUT_DIR="./output/$TIMESTAMP"
mkdir -p "$OUTPUT_DIR"

echo "=============================="
echo "  Job Scraper - $TIMESTAMP"
echo "=============================="

# ─── Trustme ───────────────────────────────────────────
echo ""
echo "[1/4] Scraping Trustme..."
docker run --rm \
  --name scraper_trustme \
  --network job_network \
  -v "$(pwd)/output:/app/output" \
  job_scrapper \
  sh -c "cd /app/trustme_scraper && scrapy crawl trustme -o /app/output/$TIMESTAMP/trustme.json 2>&1" \
  && echo "✅ Trustme done" || echo "❌ Trustme failed"

# ─── Emploitic ─────────────────────────────────────────
echo ""
echo "[2/4] Scraping Emploitic..."
docker run --rm \
  --name scraper_emploitic \
  --network job_network \
  -v "$(pwd)/output:/app/output" \
  job_scrapper \
  sh -c "cd /app/emploitic_scraper && scrapy crawl emploitic -o /app/output/$TIMESTAMP/emploitic.json 2>&1" \
  && echo "✅ Emploitic done" || echo "❌ Emploitic failed"

# ─── EmploiPartner ─────────────────────────────────────
echo ""
echo "[3/4] Scraping EmploiPartner..."
docker run --rm \
  --name scraper_emploipartner \
  --network job_network \
  -v "$(pwd)/output:/app/output" \
  job_scrapper \
  sh -c "cd /app/emploipartner_scraper && scrapy crawl emploipartner -o /app/output/$TIMESTAMP/emploipartner.json 2>&1" \
  && echo "✅ EmploiPartner done" || echo "❌ EmploiPartner failed"

# ─── AlgerieJob ────────────────────────────────────────
echo ""
echo "[4/4] Scraping AlgerieJob..."
docker run --rm \
  --name scraper_algeriejob \
  --network job_network \
  -v "$(pwd)/output:/app/output" \
  job_scrapper \
  sh -c "cd /app/algeriejob_scraper && scrapy crawl algeriejob -o /app/output/$TIMESTAMP/algeriejob.json 2>&1" \
  && echo "✅ AlgerieJob done" || echo "❌ AlgerieJob failed"

# ─── Summary ───────────────────────────────────────────
echo ""
echo "=============================="
echo "  All scrapers finished!"
echo "  Output: $OUTPUT_DIR"
echo "=============================="

# Count total jobs saved to DB
docker exec postgres_db psql -U admin -d job_scrapper -c \
  "SELECT source_name, total_jobs, last_scraped FROM stats_per_source;" 2>/dev/null \
  || echo "(Could not fetch DB stats)"
