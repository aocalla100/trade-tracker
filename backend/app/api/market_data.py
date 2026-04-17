from typing import Optional
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.session import get_db
from app.services.webull_service import WebullService

router = APIRouter()


def get_webull() -> WebullService:
    return WebullService()


@router.get("/snapshot/{symbol}")
async def get_snapshot(symbol: str, webull: WebullService = Depends(get_webull)):
    """Get real-time snapshot for a symbol."""
    try:
        data = webull.get_snapshot(symbol.upper())
        return data
    except Exception as e:
        raise HTTPException(502, f"Webull API error: {str(e)}")


@router.get("/bars/{symbol}")
async def get_bars(
    symbol: str,
    timespan: str = "D1",
    count: int = 30,
    webull: WebullService = Depends(get_webull),
):
    """Get historical OHLCV bars."""
    try:
        data = webull.get_history_bars(symbol.upper(), timespan, count)
        return data
    except Exception as e:
        raise HTTPException(502, f"Webull API error: {str(e)}")


@router.get("/options-chain/{symbol}")
async def get_options_chain(
    symbol: str,
    expiration: Optional[str] = None,
    webull: WebullService = Depends(get_webull),
):
    """Get options chain data for opportunity evaluation."""
    try:
        data = webull.get_options_chain(symbol.upper(), expiration)
        return data
    except Exception as e:
        raise HTTPException(502, f"Webull API error: {str(e)}")
