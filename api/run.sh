#!/bin/bash

set -e

IMAGE_NAME="job_scrapper_api"
CONTAINER_NAME="job_api"
PORT=8000

echo "=============================="
echo "  Job Scrapper API"
echo "=============================="

# ─── Stop and remove old container if running ─────────────────────────────────
if [ "$(docker ps -q -f name=$CONTAINER_NAME)" ]; then
    echo "⏹  Stopping running container..."
    docker stop $CONTAINER_NAME
fi

if [ "$(docker ps -aq -f name=$CONTAINER_NAME)" ]; then
    echo "🗑  Removing old container..."
    docker rm $CONTAINER_NAME
fi

# ─── Remove old image to force rebuild ────────────────────────────────────────
if [ "$(docker images -q $IMAGE_NAME)" ]; then
    echo "🗑  Removing old image..."
    docker rmi $IMAGE_NAME
fi

# ─── Build new image ──────────────────────────────────────────────────────────
echo ""
echo "🔨 Building image..."
docker build -t $IMAGE_NAME .

# ─── Start container ──────────────────────────────────────────────────────────
echo ""
echo "🚀 Starting API container..."
docker run -d \
    --name $CONTAINER_NAME \
    --network job_network \
    --restart unless-stopped \
    -p $PORT:8000 \
    $IMAGE_NAME

# ─── Wait for API to be ready ─────────────────────────────────────────────────
echo ""
echo "⏳ Waiting for API to start..."
sleep 3

# ─── Health check ─────────────────────────────────────────────────────────────
HEALTH=$(curl -s http://localhost:$PORT/ || echo "failed")

if echo "$HEALTH" | grep -q "running"; then
    echo ""
    echo "=============================="
    echo "✅ API is running!"
    echo "=============================="
    echo ""
    echo "  Local:   http://localhost:$PORT"
    echo "  Docs:    http://localhost:$PORT/docs"
    echo "  API Key: scraper-admin-secret-2026"
    echo ""
else
    echo ""
    echo "❌ API failed to start. Check logs:"
    echo "   docker logs $CONTAINER_NAME"
    exit 1
fi
