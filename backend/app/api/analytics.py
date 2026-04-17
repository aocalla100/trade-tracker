from datetime import datetime
from typing import Optional
from fastapi import APIRouter, Depends, Query
from sqlalchemy import select, func, case, and_
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.session import get_db
from app.db.models import Trade, TradeStatus

router = APIRouter()


@router.get("/strategy")
async def strategy_analysis(
    db: AsyncSession = Depends(get_db),
    strategy: Optional[str] = None,
    from_date: Optional[datetime] = None,
    to_date: Optional[datetime] = None,
):
    """Win rate, average return, and expectancy per strategy."""
    base_filter = [Trade.status == TradeStatus.CLOSED]
    if strategy:
        base_filter.append(Trade.strategy_name == strategy)
    if from_date:
        base_filter.append(Trade.entry_timestamp >= from_date)
    if to_date:
        base_filter.append(Trade.entry_timestamp <= to_date)

    q = select(
        Trade.strategy_name,
        func.count(Trade.id).label("total_trades"),
        func.count(case((Trade.realized_pnl > 0, 1))).label("wins"),
        func.count(case((Trade.realized_pnl <= 0, 1))).label("losses"),
        func.avg(Trade.realized_pnl).label("avg_pnl"),
        func.avg(Trade.realized_pnl_pct).label("avg_pnl_pct"),
        func.sum(Trade.realized_pnl).label("total_pnl"),
        func.avg(case((Trade.realized_pnl > 0, Trade.realized_pnl))).label("avg_win"),
        func.avg(case((Trade.realized_pnl <= 0, Trade.realized_pnl))).label("avg_loss"),
    ).where(and_(*base_filter)).group_by(Trade.strategy_name)

    result = await db.execute(q)
    rows = result.all()

    strategies = []
    for row in rows:
        win_rate = row.wins / row.total_trades if row.total_trades > 0 else 0
        avg_win = float(row.avg_win or 0)
        avg_loss = abs(float(row.avg_loss or 0))
        expectancy = (win_rate * avg_win) - ((1 - win_rate) * avg_loss)

        strategies.append({
            "strategy_name": row.strategy_name,
            "total_trades": row.total_trades,
            "wins": row.wins,
            "losses": row.losses,
            "win_rate": round(win_rate * 100, 2),
            "avg_pnl": round(float(row.avg_pnl or 0), 2),
            "avg_pnl_pct": round(float(row.avg_pnl_pct or 0), 2),
            "total_pnl": round(float(row.total_pnl or 0), 2),
            "expectancy": round(expectancy, 2),
        })

    return strategies


@router.get("/greeks")
async def greeks_analysis(
    db: AsyncSession = Depends(get_db),
    from_date: Optional[datetime] = None,
    to_date: Optional[datetime] = None,
):
    """Delta exposure at entry vs outcome, theta decay captured vs expected."""
    base_filter = [Trade.status == TradeStatus.CLOSED]
    if from_date:
        base_filter.append(Trade.entry_timestamp >= from_date)
    if to_date:
        base_filter.append(Trade.entry_timestamp <= to_date)

    q = select(Trade).where(and_(*base_filter))
    result = await db.execute(q)
    trades = result.scalars().all()

    analysis = []
    for t in trades:
        if t.entry_delta is None:
            continue
        analysis.append({
            "trade_id": str(t.id),
            "symbol": t.underlying_symbol,
            "strategy": t.strategy_name,
            "entry_delta": t.entry_delta,
            "exit_delta": t.exit_delta,
            "entry_theta": t.entry_theta,
            "exit_theta": t.exit_theta,
            "entry_vega": t.entry_vega,
            "entry_iv": t.entry_iv,
            "exit_iv": t.exit_iv,
            "realized_pnl": t.realized_pnl,
            "theta_captured": (
                (t.entry_theta - (t.exit_theta or 0))
                if t.entry_theta else None
            ),
            "iv_change": (
                (t.exit_iv - t.entry_iv)
                if t.entry_iv and t.exit_iv else None
            ),
        })

    return {
        "trades_analyzed": len(analysis),
        "avg_entry_delta": (
            round(sum(a["entry_delta"] for a in analysis) / len(analysis), 4)
            if analysis else None
        ),
        "details": analysis,
    }


@router.get("/behavior")
async def behavioral_analysis(
    db: AsyncSession = Depends(get_db),
    from_date: Optional[datetime] = None,
    to_date: Optional[datetime] = None,
):
    """Plan adherence, early vs late exits, execution consistency."""
    base_filter = [Trade.status == TradeStatus.CLOSED]
    if from_date:
        base_filter.append(Trade.entry_timestamp >= from_date)
    if to_date:
        base_filter.append(Trade.entry_timestamp <= to_date)

    q = select(Trade).where(and_(*base_filter))
    result = await db.execute(q)
    trades = result.scalars().all()

    total = len(trades)
    if total == 0:
        return {"total_trades": 0, "plan_adherence_rate": None, "details": []}

    followed_plan = 0
    early_exits = 0
    late_exits = 0

    for t in trades:
        review = t.post_review or {}
        if review.get("followed_plan"):
            followed_plan += 1
        exit_timing = review.get("exit_timing", "")
        if exit_timing == "early":
            early_exits += 1
        elif exit_timing == "late":
            late_exits += 1

    return {
        "total_trades": total,
        "plan_adherence_rate": round(followed_plan / total * 100, 2),
        "early_exits": early_exits,
        "late_exits": late_exits,
        "on_time_exits": total - early_exits - late_exits,
    }
