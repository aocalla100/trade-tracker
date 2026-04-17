import json
import logging
from datetime import datetime, timedelta
from typing import Any

from sqlalchemy import select, func, desc
from sqlalchemy.ext.asyncio import AsyncSession

from app.config import get_settings
from app.db.models import (
    Trade, TimeSeriesSnapshot, Position, WsbSentiment, AiInsightLog, TradeStatus,
)
from app.prompts.system_prompt import build_system_prompt
from app.prompts.tool_definitions import TOOL_DEFINITIONS

logger = logging.getLogger(__name__)
settings = get_settings()


class AiService:
    def __init__(self, db: AsyncSession):
        import anthropic
        self._client = anthropic.Anthropic(api_key=settings.anthropic_api_key)
        self._db = db
        self._model = "claude-sonnet-4-20250514"

    async def chat(self, user_message: str) -> str:
        """Run a full agentic loop: Claude calls tools, we execute, repeat."""
        messages = [{"role": "user", "content": user_message}]

        for _ in range(10):  # max tool-use turns
            response = self._client.messages.create(
                model=self._model,
                max_tokens=4096,
                system=build_system_prompt(),
                tools=TOOL_DEFINITIONS,
                messages=messages,
            )

            if response.stop_reason == "end_turn":
                return self._extract_text(response)

            if response.stop_reason == "tool_use":
                messages.append({"role": "assistant", "content": response.content})

                tool_results = []
                for block in response.content:
                    if block.type == "tool_use":
                        result = await self._execute_tool(block.name, block.input)
                        tool_results.append({
                            "type": "tool_result",
                            "tool_use_id": block.id,
                            "content": json.dumps(result, default=str),
                        })

                messages.append({"role": "user", "content": tool_results})
            else:
                return self._extract_text(response)

        return "I reached the maximum number of tool calls. Here's what I found so far."

    async def generate_proactive_insights(self) -> list[dict]:
        """Run periodic insight generation prompts."""
        prompts = [
            {
                "type": "performance_review",
                "message": (
                    "Review my trades from the last 7 days. Flag any changes in "
                    "performance, strategy drift, or behavioral patterns worth noting."
                ),
            },
            {
                "type": "opportunity_scan",
                "message": (
                    "Given my current positions and recent market data, are there any "
                    "TastyTrade-style opportunities? Look for 45 DTE, high IV environments, "
                    "credit spreads, or covered call setups on my core holdings."
                ),
            },
            {
                "type": "wsb_scan",
                "message": (
                    "Check the latest WSB sentiment data. Are there any tickers with "
                    "unusual bullish momentum spikes worth flagging as Bets? Remember these "
                    "are separate from my core strategies."
                ),
            },
        ]

        insights = []
        for prompt in prompts:
            try:
                response = await self.chat(prompt["message"])
                insight = AiInsightLog(
                    insight_type=prompt["type"],
                    content=response,
                    related_symbols=[],
                )
                self._db.add(insight)
                await self._db.commit()
                insights.append({
                    "type": prompt["type"],
                    "content": response,
                })
            except Exception as e:
                logger.error("Insight generation failed for %s: %s", prompt["type"], e)

        return insights

    async def _execute_tool(self, name: str, input_data: dict) -> Any:
        """Execute a tool call and return the result."""
        handlers = {
            "query_trades": self._tool_query_trades,
            "get_trade_detail": self._tool_get_trade_detail,
            "get_performance_summary": self._tool_get_performance_summary,
            "get_positions": self._tool_get_positions,
            "get_wsb_sentiment": self._tool_get_wsb_sentiment,
            "get_portfolio_summary": self._tool_get_portfolio_summary,
        }

        handler = handlers.get(name)
        if not handler:
            return {"error": f"Unknown tool: {name}"}

        try:
            return await handler(input_data)
        except Exception as e:
            logger.error("Tool %s failed: %s", name, e)
            return {"error": str(e), "is_error": True}

    async def _tool_query_trades(self, params: dict) -> list[dict]:
        q = select(Trade).order_by(desc(Trade.entry_timestamp)).limit(params.get("limit", 20))
        if params.get("symbol"):
            q = q.where(Trade.underlying_symbol == params["symbol"].upper())
        if params.get("strategy"):
            q = q.where(Trade.strategy_name == params["strategy"])
        if params.get("status"):
            q = q.where(Trade.status == params["status"])
        if params.get("days_back"):
            cutoff = datetime.utcnow() - timedelta(days=params["days_back"])
            q = q.where(Trade.entry_timestamp >= cutoff)

        result = await self._db.execute(q)
        trades = result.scalars().all()
        return [
            {
                "id": str(t.id),
                "symbol": t.underlying_symbol,
                "strategy": t.strategy_name,
                "direction": t.direction,
                "entry_price": t.entry_price,
                "exit_price": t.exit_price,
                "realized_pnl": t.realized_pnl,
                "status": t.status,
                "entry_timestamp": str(t.entry_timestamp),
                "tags": t.tags,
            }
            for t in trades
        ]

    async def _tool_get_trade_detail(self, params: dict) -> dict:
        result = await self._db.execute(
            select(Trade).where(Trade.id == params["trade_id"])
        )
        t = result.scalar_one_or_none()
        if not t:
            return {"error": "Trade not found"}
        return {
            "id": str(t.id),
            "symbol": t.underlying_symbol,
            "strategy": t.strategy_name,
            "position_type": t.position_type,
            "direction": t.direction,
            "quantity": t.quantity,
            "entry_price": t.entry_price,
            "exit_price": t.exit_price,
            "entry_iv": t.entry_iv,
            "exit_iv": t.exit_iv,
            "entry_delta": t.entry_delta,
            "entry_theta": t.entry_theta,
            "entry_vega": t.entry_vega,
            "realized_pnl": t.realized_pnl,
            "realized_pnl_pct": t.realized_pnl_pct,
            "trade_thesis": t.trade_thesis,
            "invalidation_conditions": t.invalidation_conditions,
            "post_review": t.post_review,
            "status": t.status,
        }

    async def _tool_get_performance_summary(self, params: dict) -> dict:
        days_back = params.get("days_back", 30)
        cutoff = datetime.utcnow() - timedelta(days=days_back)

        q = select(Trade).where(
            Trade.status == TradeStatus.CLOSED,
            Trade.exit_timestamp >= cutoff,
        )
        result = await self._db.execute(q)
        trades = result.scalars().all()

        if not trades:
            return {"total_trades": 0, "message": "No closed trades in this period."}

        wins = [t for t in trades if t.realized_pnl and t.realized_pnl > 0]
        losses = [t for t in trades if t.realized_pnl and t.realized_pnl <= 0]
        total_pnl = sum(t.realized_pnl or 0 for t in trades)

        strategies = {}
        for t in trades:
            s = strategies.setdefault(t.strategy_name, {"wins": 0, "losses": 0, "pnl": 0})
            if t.realized_pnl and t.realized_pnl > 0:
                s["wins"] += 1
            else:
                s["losses"] += 1
            s["pnl"] += t.realized_pnl or 0

        return {
            "period_days": days_back,
            "total_trades": len(trades),
            "wins": len(wins),
            "losses": len(losses),
            "win_rate": round(len(wins) / len(trades) * 100, 2),
            "total_pnl": round(total_pnl, 2),
            "by_strategy": strategies,
        }

    async def _tool_get_positions(self, _params: dict) -> list[dict]:
        result = await self._db.execute(select(Position))
        positions = result.scalars().all()
        return [
            {
                "symbol": p.symbol,
                "quantity": p.quantity,
                "avg_cost": p.avg_cost,
                "current_value": p.current_value,
                "unrealized_pnl": p.unrealized_pnl,
                "type": p.position_type,
            }
            for p in positions
        ]

    async def _tool_get_wsb_sentiment(self, params: dict) -> list[dict]:
        q = (
            select(WsbSentiment)
            .order_by(desc(WsbSentiment.scraped_at))
            .limit(params.get("limit", 20))
        )
        if params.get("spikes_only"):
            q = q.where(WsbSentiment.is_spike == True)
        result = await self._db.execute(q)
        rows = result.scalars().all()
        return [
            {
                "symbol": r.symbol,
                "mention_count": r.mention_count,
                "avg_sentiment": r.avg_sentiment,
                "is_spike": r.is_spike,
                "scraped_at": str(r.scraped_at),
            }
            for r in rows
        ]

    async def _tool_get_portfolio_summary(self, _params: dict) -> dict:
        pos_result = await self._db.execute(select(Position))
        positions = pos_result.scalars().all()

        open_result = await self._db.execute(
            select(Trade).where(Trade.status == TradeStatus.OPEN)
        )
        open_trades = open_result.scalars().all()

        total_value = sum(p.current_value or 0 for p in positions)
        total_cost = sum(p.avg_cost * p.quantity for p in positions)
        unrealized = sum(p.unrealized_pnl or 0 for p in positions)

        return {
            "core_positions": [
                {"symbol": p.symbol, "qty": p.quantity, "value": p.current_value}
                for p in positions
            ],
            "total_portfolio_value": round(total_value, 2),
            "total_cost_basis": round(total_cost, 2),
            "total_unrealized_pnl": round(unrealized, 2),
            "open_trades": len(open_trades),
        }

    @staticmethod
    def _extract_text(response) -> str:
        parts = []
        for block in response.content:
            if hasattr(block, "text"):
                parts.append(block.text)
        return "\n".join(parts) if parts else ""
