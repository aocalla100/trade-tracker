"""Map Webull OpenAPI positions into Trade journal rows and sync idempotently."""

from __future__ import annotations

import logging
import re
from datetime import datetime, timezone
from typing import Any, Optional

from sqlalchemy import select, and_
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.models import Trade, TradeStatus, PositionType, Direction
from app.services.webull_service import WebullService

logger = logging.getLogger(__name__)

_PLACEHOLDER_THESIS = (
    "Imported from Webull OpenAPI. Replace this with your actual trade thesis when you review."
)
_PLACEHOLDER_RATIONALE = (
    "Auto-imported from your live broker position (cost basis and quantity from Webull)."
)
_PLACEHOLDER_INVALIDATION = (
    "Define invalidation criteria when you review this import."
)


def _parse_decimal(value: str | None) -> float:
    if value is None or value == "":
        return 0.0
    try:
        return float(value)
    except (TypeError, ValueError):
        return 0.0


def _parse_int_qty(value: str | None) -> int:
    if value is None or value == "":
        return 0
    try:
        return int(float(value))
    except (TypeError, ValueError):
        return 0


def _underlying_from_symbol(symbol: str) -> str:
    """Best-effort underlying ticker for equities or OCC option symbols."""
    s = (symbol or "").upper().strip()
    if not s:
        return "UNK"
    if len(s) <= 6 and s.replace(".", "").isalpha():
        return s[:10]
    m = re.match(r"^([A-Z]{1,5})(\d{6})([CP])", s)
    if m:
        return m.group(1)[:10]
    letters = re.match(r"^([A-Z\.]+)", s)
    if letters:
        return letters.group(1)[:10]
    return s[:10]


def _map_position_type(instrument_type: str | None, option_strategy: str | None) -> PositionType:
    t = (instrument_type or "EQUITY").upper()
    if t == "EQUITY":
        return PositionType.STOCK
    if t == "OPTION":
        strat = (option_strategy or "SINGLE").upper()
        if strat in (
            "VERTICAL", "STRADDLE", "STRANGLE", "CALENDAR", "CONDOR",
            "IRON_CONDOR", "IRON_BUTTERFLY", "BUTTERFLY", "DIAGONAL",
        ):
            return PositionType.SPREAD
        return PositionType.OPTION
    if t == "FUTURES":
        return PositionType.FUTURE
    return PositionType.STOCK


def webull_position_to_trade_fields(
    pos: dict[str, Any],
    *,
    account_id: str,
    account_label: str,
    strategy_name: str,
) -> dict[str, Any] | None:
    """Build kwargs for Trade(...) from one Webull position object. Returns None to skip."""
    position_id = pos.get("position_id")
    if not position_id:
        logger.warning("Skipping Webull position without position_id: %s", pos)
        return None

    qty = _parse_int_qty(pos.get("quantity"))
    if qty == 0:
        return None

    direction = Direction.LONG if qty > 0 else Direction.SHORT
    abs_qty = abs(qty)

    inst = (pos.get("instrument_type") or "EQUITY").upper()
    cost = _parse_decimal(pos.get("cost_price"))
    last_px = _parse_decimal(pos.get("last_price"))
    position_type = _map_position_type(inst, pos.get("option_strategy"))

    strike_price: float | None = None
    expiration_date: datetime | None = None
    premium: float | None = None
    underlying_symbol: str

    legs = pos.get("legs") if isinstance(pos.get("legs"), list) else []
    leg0: dict[str, Any] = legs[0] if legs else {}

    if position_type in (PositionType.OPTION, PositionType.SPREAD):
        underlying_symbol = _underlying_from_symbol(
            str(leg0.get("symbol") or pos.get("symbol") or "")
        )
        strike_price = _parse_decimal(leg0.get("option_exercise_price")) or None
        if strike_price == 0.0:
            strike_price = None
        exp_raw = leg0.get("option_expire_date")
        if exp_raw:
            try:
                y, m, d = (int(x) for x in str(exp_raw).split("-")[:3])
                expiration_date = datetime(y, m, d, tzinfo=timezone.utc)
            except (ValueError, TypeError):
                expiration_date = None
        premium = cost if inst == "OPTION" else None
        entry_price = last_px if last_px else cost
    else:
        underlying_symbol = str(pos.get("symbol") or "").upper()[:10] or "UNK"
        entry_price = cost if cost else last_px

    tags = ["webull_import", inst.lower()]
    exit_plan = {
        "webull_snapshot": {
            "position_id": position_id,
            "instrument_type": inst,
            "option_strategy": pos.get("option_strategy"),
            "unrealized_profit_loss": pos.get("unrealized_profit_loss"),
            "last_price": pos.get("last_price"),
            "cost_price": pos.get("cost_price"),
        }
    }

    return {
        "strategy_name": strategy_name[:100],
        "setup_classification": "webull_sync",
        "account": account_label[:100],
        "tags": tags,
        "entry_timestamp": datetime.now(timezone.utc),
        "underlying_symbol": underlying_symbol[:10],
        "entry_price": float(entry_price),
        "entry_iv": None,
        "iv_rank": None,
        "entry_volume": None,
        "market_context": "webull_import",
        "strike_price": strike_price,
        "expiration_date": expiration_date,
        "premium": premium,
        "bid_ask_spread": None,
        "open_interest": None,
        "entry_delta": None,
        "entry_gamma": None,
        "entry_theta": None,
        "entry_vega": None,
        "entry_rho": None,
        "position_type": position_type.value,
        "direction": direction.value,
        "quantity": abs_qty,
        "max_risk": None,
        "max_profit": None,
        "buying_power_used": None,
        "trade_thesis": _PLACEHOLDER_THESIS,
        "entry_rationale": _PLACEHOLDER_RATIONALE,
        "defined_edge": None,
        "invalidation_conditions": _PLACEHOLDER_INVALIDATION,
        "exit_plan": exit_plan,
        "post_review": None,
        "status": TradeStatus.OPEN,
        "webull_account_id": account_id[:64],
        "webull_position_id": str(position_id)[:80],
    }


async def existing_webull_keys(
    db: AsyncSession, account_id: str, position_ids: list[str]
) -> set[str]:
    if not position_ids:
        return set()
    q = select(Trade.webull_position_id).where(
        and_(
            Trade.webull_account_id == account_id,
            Trade.webull_position_id.in_(position_ids),
            Trade.status == TradeStatus.OPEN,
        )
    )
    result = await db.execute(q)
    return {row[0] for row in result.all() if row[0]}


async def preview_webull_import(
    db: AsyncSession,
    webull: WebullService,
    *,
    account_id: str | None,
    strategy_name: str,
) -> dict[str, Any]:
    accounts = webull.list_accounts()
    if not accounts:
        return {"error": "no_accounts", "accounts": [], "would_create": [], "skipped": []}

    resolved_id = account_id
    if not resolved_id:
        resolved_id = accounts[0].get("account_id")
    if not resolved_id:
        return {"error": "no_account_id", "accounts": accounts, "would_create": [], "skipped": []}

    account_label = f"Webull:{resolved_id[:8]}…" if len(resolved_id) > 8 else f"Webull:{resolved_id}"
    positions = webull.get_account_positions(resolved_id)
    existing = await existing_webull_keys(
        db, resolved_id, [str(p.get("position_id")) for p in positions if p.get("position_id")]
    )

    would_create: list[dict[str, Any]] = []
    skipped: list[dict[str, Any]] = []
    for pos in positions:
        pid = pos.get("position_id")
        if not pid:
            skipped.append({"reason": "missing_position_id", "raw": pos})
            continue
        if str(pid) in existing:
            skipped.append({"reason": "already_imported_open", "position_id": pid})
            continue
        fields = webull_position_to_trade_fields(
            pos,
            account_id=resolved_id,
            account_label=account_label,
            strategy_name=strategy_name,
        )
        if not fields:
            skipped.append({"reason": "zero_qty_or_unmapped", "position_id": pid})
            continue
        would_create.append(
            {
                "position_id": pid,
                "symbol": fields["underlying_symbol"],
                "quantity": fields["quantity"],
                "direction": fields["direction"],
                "position_type": fields["position_type"],
                "entry_price": fields["entry_price"],
            }
        )

    return {
        "account_id": resolved_id,
        "accounts": [{"account_id": a.get("account_id")} for a in accounts],
        "would_create": would_create,
        "skipped": skipped,
    }


async def run_webull_import(
    db: AsyncSession,
    webull: WebullService,
    *,
    account_id: str | None,
    strategy_name: str,
) -> dict[str, Any]:
    preview = await preview_webull_import(
        db, webull, account_id=account_id, strategy_name=strategy_name
    )
    if preview.get("error"):
        return preview

    resolved_id = preview["account_id"]
    account_label = (
        f"Webull:{resolved_id[:8]}…"
        if len(resolved_id) > 8
        else f"Webull:{resolved_id}"
    )
    positions = webull.get_account_positions(resolved_id)
    existing = await existing_webull_keys(
        db,
        resolved_id,
        [str(p.get("position_id")) for p in positions if p.get("position_id")],
    )

    new_trades: list[Trade] = []
    for pos in positions:
        pid = pos.get("position_id")
        if not pid or str(pid) in existing:
            continue
        fields = webull_position_to_trade_fields(
            pos,
            account_id=resolved_id,
            account_label=account_label,
            strategy_name=strategy_name,
        )
        if not fields:
            continue
        trade = Trade(**fields)
        db.add(trade)
        new_trades.append(trade)
        existing.add(str(pid))

    await db.flush()
    trade_ids = [str(t.id) for t in new_trades]
    await db.commit()
    return {
        "account_id": resolved_id,
        "imported": len(trade_ids),
        "trade_ids": trade_ids,
    }
