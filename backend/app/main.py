from contextlib import asynccontextmanager
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.api import trades, positions, analytics, insights, market_data, sentiment


@asynccontextmanager
async def lifespan(app: FastAPI):
    from app.jobs.scheduler import start_scheduler
    scheduler = start_scheduler()
    yield
    scheduler.shutdown()


app = FastAPI(
    title="Trade Tracker API",
    description="Trading journal and performance analytics with AI-powered insights",
    version="0.1.0",
    lifespan=lifespan,
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:3000",
        "http://127.0.0.1:3000",
        "http://localhost:3001",
        "http://127.0.0.1:3001",
    ],
    allow_origin_regex=r"https://.*\.pages\.dev",
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(trades.router, prefix="/api/trades", tags=["trades"])
app.include_router(positions.router, prefix="/api/positions", tags=["positions"])
app.include_router(analytics.router, prefix="/api/analytics", tags=["analytics"])
app.include_router(insights.router, prefix="/api/insights", tags=["insights"])
app.include_router(market_data.router, prefix="/api/market-data", tags=["market-data"])
app.include_router(sentiment.router, prefix="/api/sentiment", tags=["sentiment"])


@app.get("/api/health")
async def health():
    return {"status": "ok"}
