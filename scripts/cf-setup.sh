#!/usr/bin/env bash
set -euo pipefail

# Cloudflare Infrastructure Setup
# Requires: CLOUDFLARE_API_TOKEN, CLOUDFLARE_ACCOUNT_ID, DATABASE_URL

: "${CLOUDFLARE_API_TOKEN:?Set CLOUDFLARE_API_TOKEN}"
: "${CLOUDFLARE_ACCOUNT_ID:?Set CLOUDFLARE_ACCOUNT_ID}"

export CLOUDFLARE_API_TOKEN
export CLOUDFLARE_ACCOUNT_ID

echo "==> Creating Cloudflare Pages project..."
npx wrangler pages project create trade-tracker \
  --production-branch main \
  2>/dev/null || echo "    (project may already exist)"

echo "==> Setting Pages environment variables..."
echo "$NEXT_PUBLIC_API_URL" | npx wrangler pages secret put NEXT_PUBLIC_API_URL \
  --project-name trade-tracker 2>/dev/null || true

if [ -n "${DATABASE_URL:-}" ]; then
  echo "==> Creating Hyperdrive configuration..."
  npx wrangler hyperdrive create trade-tracker-db \
    --connection-string="$DATABASE_URL" \
    2>/dev/null || echo "    (hyperdrive may already exist)"
fi

echo "==> Creating Cloudflare Tunnel..."
npx wrangler tunnel create trade-tracker-api \
  2>/dev/null || echo "    (tunnel may already exist)"

echo ""
echo "Setup complete. Next steps:"
echo "  1. Connect the Pages project to github.com/aocalla100/trade-tracker"
echo "  2. Configure tunnel ingress rules in cloudflared config"
echo "  3. Set DNS records for your custom domain"
