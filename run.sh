#!/bin/bash
set -e

echo "========================================"
echo "   Job Scrapper — Docker Build & Run"
echo "========================================"

GREEN='\033[0;32m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
NC='\033[0m'

IMAGE_NAME="job_scrapper"

mkdir -p output

# ── BUILD only if image doesn't exist ────────────────────────────────
if [[ "$(docker images -q $IMAGE_NAME 2>/dev/null)" == "" ]]; then
  echo -e "\n${YELLOW}[1/2] Image not found. Building...${NC}"
  docker build -t $IMAGE_NAME .
  echo -e "${GREEN}✅ Image built successfully${NC}"
else
  echo -e "\n${GREEN}[1/2] Image already exists, skipping build ✅${NC}"
  echo -e "      Run 'docker rmi $IMAGE_NAME' to force rebuild"
fi

# ── RUN ───────────────────────────────────────────────────────────────
echo -e "\n${YELLOW}[2/2] Choose which scraper to run:${NC}"
echo "  1) algeriejob    (Playwright)"
echo "  2) trustme       (Scrapy)"
echo "  3) emploitic     (Scrapy)"
echo "  4) emploipartner (Scrapy)"
echo "  5) ALL scrapers"
echo "  6) Rebuild image"
echo ""
read -p "Enter choice [1-6]: " choice

RUN="docker run --rm -v $(pwd)/output:/app/output $IMAGE_NAME"

case $choice in
  1) echo -e "\n${YELLOW}Running algeriejob...${NC}"
     $RUN python trustme_scraper/trustme_scraper/standalone/scrape_algeriejob.py ;;
  2) echo -e "\n${YELLOW}Running trustme...${NC}"
     $RUN sh -c "cd /app/trustme_scraper && scrapy crawl trustme -o /app/output/trustme.json" ;;
  3) echo -e "\n${YELLOW}Running emploitic...${NC}"
     $RUN sh -c "cd /app/trustme_scraper && scrapy crawl emploitic -o /app/output/emploitic.json" ;;
  4) echo -e "\n${YELLOW}Running emploipartner...${NC}"
     $RUN sh -c "cd /app/trustme_scraper && scrapy crawl emploipartner -o /app/output/emploipartner.json" ;;
  5) echo -e "\n${YELLOW}Running ALL scrapers...${NC}"
     $RUN sh -c "cd /app/trustme_scraper && \
       scrapy crawl trustme -o /app/output/trustme.json & \
       scrapy crawl emploitic -o /app/output/emploitic.json & \
       scrapy crawl emploipartner -o /app/output/emploipartner.json & \
       python /app/trustme_scraper/trustme_scraper/standalone/scrape_algeriejob.py && wait" ;;
  6) echo -e "\n${YELLOW}Rebuilding image...${NC}"
     docker rmi $IMAGE_NAME 2>/dev/null || true
     docker build -t $IMAGE_NAME .
     echo -e "${GREEN}✅ Rebuilt successfully${NC}" ;;
  *) echo -e "${RED}Invalid choice. Exiting.${NC}" ; exit 1 ;;
esac

echo -e "\n${GREEN}========================================"
echo "✅ Done! Results in ./output/"
echo "========================================"
ls -lh output/ 2>/dev/null || echo "No output files yet"
echo -e "${NC}"
