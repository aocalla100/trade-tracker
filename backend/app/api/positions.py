import uuid
from typing import Optional
from datetime import datetime
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from pydantic import BaseModel

from app.db.session import get_db
from app.db.models import Position

router = APIRouter()


class PositionCreate(BaseModel):
    symbol: str
    quantity: float
    avg_cost: float
    position_type: str = "core_hold"
    notes: Optional[str] = None


class PositionUpdate(BaseModel):
    quantity: Optional[float] = None
    avg_cost: Optional[float] = None
    current_value: Optional[float] = None
    notes: Optional[str] = None


class PositionResponse(BaseModel):
    model_config = {"from_attributes": True}

    id: uuid.UUID
    symbol: str
    quantity: float
    avg_cost: float
    current_value: Optional[float]
    unrealized_pnl: Optional[float]
    position_type: str
    notes: Optional[str]
    updated_at: datetime


@router.post("", response_model=PositionResponse, status_code=201)
async def create_position(payload: PositionCreate, db: AsyncSession = Depends(get_db)):
    position = Position(**payload.model_dump())
    position.symbol = position.symbol.upper()
    db.add(position)
    await db.commit()
    await db.refresh(position)
    return position


@router.get("", response_model=list[PositionResponse])
async def list_positions(db: AsyncSession = Depends(get_db)):
    result = await db.execute(select(Position).order_by(Position.symbol))
    return result.scalars().all()


@router.get("/{symbol}", response_model=PositionResponse)
async def get_position(symbol: str, db: AsyncSession = Depends(get_db)):
    result = await db.execute(select(Position).where(Position.symbol == symbol.upper()))
    position = result.scalar_one_or_none()
    if not position:
        raise HTTPException(404, "Position not found")
    return position


@router.patch("/{symbol}", response_model=PositionResponse)
async def update_position(
    symbol: str, payload: PositionUpdate, db: AsyncSession = Depends(get_db)
):
    result = await db.execute(select(Position).where(Position.symbol == symbol.upper()))
    position = result.scalar_one_or_none()
    if not position:
        raise HTTPException(404, "Position not found")

    data = payload.model_dump(exclude_unset=True)
    for key, value in data.items():
        setattr(position, key, value)

    if position.current_value is not None:
        position.unrealized_pnl = (position.current_value - position.avg_cost) * position.quantity

    await db.commit()
    await db.refresh(position)
    return position
