from typing import Optional
from fastapi import APIRouter, Depends, Query
from sqlalchemy import select, desc
from sqlalchemy.ext.asyncio import AsyncSession
from pydantic import BaseModel

from app.db.session import get_db
from app.db.models import AiInsightLog
from app.services.ai_service import AiService

router = APIRouter()


class ChatRequest(BaseModel):
    message: str


class InsightResponse(BaseModel):
    model_config = {"from_attributes": True}

    id: str
    insight_type: str
    content: str
    related_symbols: Optional[list[str]]
    created_at: str


@router.post("/chat")
async def chat(payload: ChatRequest, db: AsyncSession = Depends(get_db)):
    """Send a message to Claude with full access to trade data via tools."""
    ai = AiService(db)
    response = await ai.chat(payload.message)
    return {"response": response}


@router.get("/feed")
async def insight_feed(
    db: AsyncSession = Depends(get_db),
    insight_type: Optional[str] = None,
    limit: int = Query(20, le=100),
):
    """Get proactive AI insight feed."""
    q = select(AiInsightLog).order_by(desc(AiInsightLog.created_at))
    if insight_type:
        q = q.where(AiInsightLog.insight_type == insight_type)
    q = q.limit(limit)
    result = await db.execute(q)
    return result.scalars().all()


@router.post("/generate")
async def generate_insights(db: AsyncSession = Depends(get_db)):
    """Manually trigger proactive insight generation."""
    ai = AiService(db)
    insights = await ai.generate_proactive_insights()
    return {"insights_generated": len(insights), "insights": insights}
