#!/usr/bin/env bash
set -euo pipefail

# Deploy backend and restart Cloudflare Tunnel
# Requires: CLOUDFLARE_API_TOKEN

: "${CLOUDFLARE_API_TOKEN:?Set CLOUDFLARE_API_TOKEN}"

export CLOUDFLARE_API_TOKEN

echo "==> Building backend Docker image..."
docker build -t trade-tracker-backend ./backend

echo "==> Backend image built successfully"
echo ""
echo "To deploy:"
echo "  - Push to your container registry and deploy to Railway/Fly.io"
echo "  - Or run locally: docker-compose up -d"
echo ""
echo "==> Deploying frontend to Cloudflare Pages..."
cd frontend
npm run build
npx wrangler pages deploy .next --project-name trade-tracker
echo "==> Frontend deployed"
