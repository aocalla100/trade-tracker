import uuid
from datetime import datetime
from typing import Optional
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy import select, func
from sqlalchemy.ext.asyncio import AsyncSession
from pydantic import BaseModel, Field

from app.config import get_settings
from app.db.session import get_db
from app.db.models import Trade, TimeSeriesSnapshot, TradeStatus
from app.services.webull_service import WebullService, get_webull
from app.services.webull_trade_sync import preview_webull_import, run_webull_import

router = APIRouter()


# --- Schemas ---

class TradeCreate(BaseModel):
    strategy_name: str
    setup_classification: Optional[str] = None
    account: str
    tags: Optional[list[str]] = []
    entry_timestamp: datetime
    underlying_symbol: str
    entry_price: float
    entry_iv: Optional[float] = None
    iv_rank: Optional[float] = None
    entry_volume: Optional[int] = None
    market_context: Optional[str] = None
    strike_price: Optional[float] = None
    expiration_date: Optional[datetime] = None
    premium: Optional[float] = None
    bid_ask_spread: Optional[float] = None
    open_interest: Optional[int] = None
    entry_delta: Optional[float] = None
    entry_gamma: Optional[float] = None
    entry_theta: Optional[float] = None
    entry_vega: Optional[float] = None
    entry_rho: Optional[float] = None
    position_type: str
    direction: str
    quantity: int
    max_risk: Optional[float] = None
    max_profit: Optional[float] = None
    buying_power_used: Optional[float] = None
    trade_thesis: str
    entry_rationale: str
    defined_edge: Optional[str] = None
    invalidation_conditions: str
    exit_plan: Optional[dict] = None


class TradeClose(BaseModel):
    exit_timestamp: datetime
    exit_price: float
    exit_premium: Optional[float] = None
    exit_iv: Optional[float] = None
    exit_delta: Optional[float] = None
    exit_gamma: Optional[float] = None
    exit_theta: Optional[float] = None
    exit_vega: Optional[float] = None
    post_review: Optional[dict] = None


class SnapshotCreate(BaseModel):
    timestamp: datetime
    underlying_price: float
    position_value: float
    delta: Optional[float] = None
    gamma: Optional[float] = None
    theta: Optional[float] = None
    vega: Optional[float] = None
    iv: Optional[float] = None


class TradeResponse(BaseModel):
    model_config = {"from_attributes": True}

    id: uuid.UUID
    created_at: datetime
    strategy_name: str
    setup_classification: Optional[str]
    account: str
    tags: Optional[list[str]]
    entry_timestamp: datetime
    underlying_symbol: str
    entry_price: float
    entry_iv: Optional[float]
    iv_rank: Optional[float]
    market_context: Optional[str]
    position_type: str
    direction: str
    quantity: int
    max_risk: Optional[float]
    max_profit: Optional[float]
    buying_power_used: Optional[float]
    strike_price: Optional[float]
    expiration_date: Optional[datetime]
    premium: Optional[float]
    entry_delta: Optional[float]
    entry_gamma: Optional[float]
    entry_theta: Optional[float]
    entry_vega: Optional[float]
    exit_timestamp: Optional[datetime]
    exit_price: Optional[float]
    realized_pnl: Optional[float]
    realized_pnl_pct: Optional[float]
    trade_thesis: str
    invalidation_conditions: str
    exit_plan: Optional[dict]
    post_review: Optional[dict]
    status: str
    webull_account_id: Optional[str] = None
    webull_position_id: Optional[str] = None


class WebullSyncRequest(BaseModel):
    account_id: Optional[str] = None
    strategy_name: str = "webull_positions"


class SnapshotResponse(BaseModel):
    model_config = {"from_attributes": True}

    id: uuid.UUID
    trade_id: uuid.UUID
    timestamp: datetime
    underlying_price: float
    position_value: float
    delta: Optional[float]
    gamma: Optional[float]
    theta: Optional[float]
    vega: Optional[float]
    iv: Optional[float]


# --- Immutable field sets ---

IMMUTABLE_ENTRY_FIELDS = {
    "entry_timestamp", "underlying_symbol", "entry_price", "entry_iv",
    "iv_rank", "entry_volume", "market_context", "strike_price",
    "expiration_date", "premium", "bid_ask_spread", "open_interest",
    "entry_delta", "entry_gamma", "entry_theta", "entry_vega", "entry_rho",
    "position_type", "direction", "quantity", "trade_thesis",
    "entry_rationale", "defined_edge", "invalidation_conditions",
}


# --- Endpoints ---

@router.post("", response_model=TradeResponse, status_code=201)
async def create_trade(payload: TradeCreate, db: AsyncSession = Depends(get_db)):
    trade = Trade(**payload.model_dump())
    db.add(trade)
    await db.commit()
    await db.refresh(trade)
    return trade


@router.get("", response_model=list[TradeResponse])
async def list_trades(
    db: AsyncSession = Depends(get_db),
    symbol: Optional[str] = None,
    strategy: Optional[str] = None,
    status: Optional[str] = None,
    tag: Optional[str] = None,
    from_date: Optional[datetime] = None,
    to_date: Optional[datetime] = None,
    limit: int = Query(50, le=200),
    offset: int = 0,
):
    q = select(Trade).order_by(Trade.entry_timestamp.desc())
    if symbol:
        q = q.where(Trade.underlying_symbol == symbol.upper())
    if strategy:
        q = q.where(Trade.strategy_name == strategy)
    if status:
        q = q.where(Trade.status == status)
    if tag:
        q = q.where(Trade.tags.any(tag))
    if from_date:
        q = q.where(Trade.entry_timestamp >= from_date)
    if to_date:
        q = q.where(Trade.entry_timestamp <= to_date)
    q = q.limit(limit).offset(offset)
    result = await db.execute(q)
    return result.scalars().all()


@router.get("/sync/webull/preview")
async def preview_webull_trade_import(
    account_id: Optional[str] = None,
    strategy_name: str = Query(default="webull_positions", max_length=100),
    db: AsyncSession = Depends(get_db),
    webull: WebullService = Depends(get_webull),
):
    """Dry-run: show Webull open positions that would become new journal trades."""
    settings = get_settings()
    if not settings.webull_app_key or not settings.webull_app_secret:
        raise HTTPException(400, "Webull app key and secret are not configured")
    return await preview_webull_import(
        db, webull, account_id=account_id, strategy_name=strategy_name
    )


@router.post("/sync/webull", status_code=201)
async def import_webull_trades(
    payload: WebullSyncRequest,
    db: AsyncSession = Depends(get_db),
    webull: WebullService = Depends(get_webull),
):
    """Create open Trade rows from Webull positions (skips positions already linked to an open trade)."""
    settings = get_settings()
    if not settings.webull_app_key or not settings.webull_app_secret:
        raise HTTPException(400, "Webull app key and secret are not configured")
    return await run_webull_import(
        db,
        webull,
        account_id=payload.account_id,
        strategy_name=payload.strategy_name,
    )


@router.get("/{trade_id}", response_model=TradeResponse)
async def get_trade(trade_id: uuid.UUID, db: AsyncSession = Depends(get_db)):
    result = await db.execute(select(Trade).where(Trade.id == trade_id))
    trade = result.scalar_one_or_none()
    if not trade:
        raise HTTPException(404, "Trade not found")
    return trade


@router.patch("/{trade_id}", response_model=TradeResponse)
async def close_trade(
    trade_id: uuid.UUID,
    payload: TradeClose,
    db: AsyncSession = Depends(get_db),
):
    """Close a trade by adding exit data. Entry snapshot fields remain immutable."""
    result = await db.execute(select(Trade).where(Trade.id == trade_id))
    trade = result.scalar_one_or_none()
    if not trade:
        raise HTTPException(404, "Trade not found")
    if trade.status == TradeStatus.CLOSED:
        raise HTTPException(400, "Trade is already closed")

    data = payload.model_dump(exclude_unset=True)
    for key, value in data.items():
        setattr(trade, key, value)

    trade.status = TradeStatus.CLOSED

    if trade.entry_price and payload.exit_price:
        if trade.direction == "long":
            trade.realized_pnl = (payload.exit_price - trade.entry_price) * trade.quantity
        else:
            trade.realized_pnl = (trade.entry_price - payload.exit_price) * trade.quantity
        if trade.entry_price != 0:
            trade.realized_pnl_pct = trade.realized_pnl / (trade.entry_price * trade.quantity) * 100
        if trade.max_risk and trade.max_risk != 0:
            trade.risk_adjusted_return = trade.realized_pnl / trade.max_risk

    await db.commit()
    await db.refresh(trade)
    return trade


@router.post("/{trade_id}/snapshots", response_model=SnapshotResponse, status_code=201)
async def add_snapshot(
    trade_id: uuid.UUID,
    payload: SnapshotCreate,
    db: AsyncSession = Depends(get_db),
):
    result = await db.execute(select(Trade).where(Trade.id == trade_id))
    if not result.scalar_one_or_none():
        raise HTTPException(404, "Trade not found")

    snapshot = TimeSeriesSnapshot(trade_id=trade_id, **payload.model_dump())
    db.add(snapshot)
    await db.commit()
    await db.refresh(snapshot)
    return snapshot


@router.get("/{trade_id}/snapshots", response_model=list[SnapshotResponse])
async def list_snapshots(trade_id: uuid.UUID, db: AsyncSession = Depends(get_db)):
    result = await db.execute(
        select(TimeSeriesSnapshot)
        .where(TimeSeriesSnapshot.trade_id == trade_id)
        .order_by(TimeSeriesSnapshot.timestamp)
    )
    return result.scalars().all()
