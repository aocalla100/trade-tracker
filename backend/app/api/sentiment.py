import uuid
from datetime import datetime
from typing import Optional
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy import select, desc, func, and_
from sqlalchemy.ext.asyncio import AsyncSession
from pydantic import BaseModel

from app.db.session import get_db
from app.db.models import WsbSentiment, Bet, BetStatus

router = APIRouter()


class BetCreate(BaseModel):
    symbol: str
    sentiment_score: float
    mention_velocity: Optional[float] = None
    source_post_ids: Optional[list[str]] = None
    notes: Optional[str] = None


class BetUpdate(BaseModel):
    status: Optional[str] = None
    notes: Optional[str] = None


class SentimentResponse(BaseModel):
    model_config = {"from_attributes": True}

    id: uuid.UUID
    symbol: str
    mention_count: int
    avg_sentiment: float
    top_posts: Optional[dict]
    scraped_at: datetime
    is_spike: bool


class BetResponse(BaseModel):
    model_config = {"from_attributes": True}

    id: uuid.UUID
    symbol: str
    source_post_ids: Optional[list[str]]
    sentiment_score: float
    mention_velocity: Optional[float]
    status: str
    notes: Optional[str]
    created_at: datetime
    updated_at: datetime


@router.get("/wsb", response_model=list[SentimentResponse])
async def list_sentiment(
    db: AsyncSession = Depends(get_db),
    symbol: Optional[str] = None,
    spikes_only: bool = False,
    limit: int = Query(50, le=200),
):
    q = select(WsbSentiment).order_by(desc(WsbSentiment.scraped_at))
    if symbol:
        q = q.where(WsbSentiment.symbol == symbol.upper())
    if spikes_only:
        q = q.where(WsbSentiment.is_spike == True)
    q = q.limit(limit)
    result = await db.execute(q)
    return result.scalars().all()


@router.get("/wsb/latest")
async def latest_spikes(db: AsyncSession = Depends(get_db)):
    """Get the most recent sentiment spike for each symbol."""
    subq = (
        select(
            WsbSentiment.symbol,
            func.max(WsbSentiment.scraped_at).label("latest"),
        )
        .where(WsbSentiment.is_spike == True)
        .group_by(WsbSentiment.symbol)
        .subquery()
    )
    q = select(WsbSentiment).join(
        subq,
        and_(
            WsbSentiment.symbol == subq.c.symbol,
            WsbSentiment.scraped_at == subq.c.latest,
        ),
    )
    result = await db.execute(q)
    return [SentimentResponse.model_validate(r) for r in result.scalars().all()]


@router.post("/bets", response_model=BetResponse, status_code=201)
async def create_bet(payload: BetCreate, db: AsyncSession = Depends(get_db)):
    bet = Bet(**payload.model_dump())
    bet.symbol = bet.symbol.upper()
    db.add(bet)
    await db.commit()
    await db.refresh(bet)
    return bet


@router.get("/bets", response_model=list[BetResponse])
async def list_bets(
    db: AsyncSession = Depends(get_db),
    status: Optional[str] = None,
    limit: int = Query(50, le=200),
):
    q = select(Bet).order_by(desc(Bet.created_at))
    if status:
        q = q.where(Bet.status == status)
    q = q.limit(limit)
    result = await db.execute(q)
    return result.scalars().all()


@router.patch("/bets/{bet_id}", response_model=BetResponse)
async def update_bet(
    bet_id: uuid.UUID, payload: BetUpdate, db: AsyncSession = Depends(get_db)
):
    result = await db.execute(select(Bet).where(Bet.id == bet_id))
    bet = result.scalar_one_or_none()
    if not bet:
        raise HTTPException(404, "Bet not found")

    data = payload.model_dump(exclude_unset=True)
    for key, value in data.items():
        setattr(bet, key, value)

    await db.commit()
    await db.refresh(bet)
    return bet
