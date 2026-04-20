# Trade Tracker

Trading journal and performance analytics platform with AI-powered insights.

## Features

- **Trade Journal**: Full trade lifecycle tracking with immutable entry/exit snapshots, time-series Greeks, and decision logging — plus **Import from Webull** to create open trades from live broker positions (deduped by Webull `position_id`)
- **Performance Analytics**: Strategy win rates, expectancy, Greeks analysis, and behavioral patterns
- **AI Insights**: Claude-powered chat with tool access to all trade data, plus proactive insight generation
- **Market Data**: Real-time and historical data via Webull OpenAPI
- **WSB Bets**: WSB mention/sentiment from ApeWisdom (API) and SwaggyStocks (optional login scrape) with spike detection — tracked separately from core strategies
- **Core Positions**: Long-term position tracking for TSLA, PLTR, and other holdings

## Tech Stack

- **Backend**: Python 3.11+, FastAPI, SQLAlchemy 2.0, Alembic, APScheduler
- **Frontend**: Next.js 14, TypeScript, Tailwind CSS, shadcn/ui, Recharts
- **Database**: PostgreSQL (Neon serverless in production)
- **AI**: Anthropic Claude API with tool use
- **Market Data**: Webull OpenAPI Python SDK
- **Sentiment**: ApeWisdom API + SwaggyStocks (optional)
- **Hosting**: Cloudflare Pages (frontend) + Cloudflare Tunnel (backend)

## Quick Start

### Prerequisites

- Python 3.11+
- Node.js 20+
- Docker (for PostgreSQL)

### Local Development

```bash
# Clone
git clone https://github.com/aocalla100/trade-tracker.git
cd trade-tracker

# Start PostgreSQL
docker-compose up db -d

# Backend
cp .env.example .env  # Fill in your API keys
cd backend
pip install -r requirements.txt
alembic upgrade head
uvicorn app.main:app --reload

# Frontend (new terminal)
cd frontend
npm install
npm run dev
```

Open http://localhost:3000

### Environment Variables

Copy `.env.example` to `.env` and fill in:
- `DATABASE_URL` — PostgreSQL connection string
- `ANTHROPIC_API_KEY` — Claude API key
- `WEBULL_APP_KEY` / `WEBULL_APP_SECRET` — Webull OpenAPI credentials
- `SWAGGYSTOCKS_USERNAME` / `SWAGGYSTOCKS_PASSWORD` — Optional; enriches sentiment from SwaggyStocks (ApeWisdom needs no key)
- `CLOUDFLARE_API_TOKEN` — For deployment
- `WEBULL_AUTO_SYNC_INTERVAL_HOURS` — How often to import new Webull positions into the journal while the API process is running (default `6`; set `0` to disable the scheduler job). `WEBULL_AUTO_SYNC_ENABLED=false` turns the job off without changing the interval.

### Local dev: terminals, CORS, and Webull import

- **Do background terminals need to stay up for days?** No. You only need `uvicorn` and `npm run dev` **while you are actively developing or using the local app**. It is safe to stop them after long runs and start again later. Scheduled Webull sync runs **inside the FastAPI process**, so when the backend is stopped, nothing syncs until you start it again. In production, run the API under a process manager or container instead of a long-lived interactive terminal.
- **“Failed to fetch” on Import from Webull** almost always means the browser could not complete the request to the API: backend not running, wrong `NEXT_PUBLIC_API_URL`, or **CORS** (e.g. site opened at `http://127.0.0.1:3000` while the API only allowed `http://localhost:3000`). Use the same host style in the URL as in the address bar, point `NEXT_PUBLIC_API_URL` at the real API origin (including port), and restart the backend after updating CORS. The API client error message in the UI now includes a short hint when the request fails at the network layer.

## Architecture

```
Frontend (Next.js) → FastAPI Backend → PostgreSQL
                         ↕
              Claude AI (tool use)
              Webull OpenAPI (market data)
              ApeWisdom + SwaggyStocks (WSB sentiment)
```

## Deployment

```bash
# One-time Cloudflare setup
export CLOUDFLARE_API_TOKEN=your_token
export CLOUDFLARE_ACCOUNT_ID=737e8715349674266a977fe6e53eb038
bash scripts/cf-setup.sh

# Deploy
bash scripts/cf-deploy.sh
```
