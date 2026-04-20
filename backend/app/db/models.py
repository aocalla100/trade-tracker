import uuid
from datetime import datetime
from sqlalchemy import (
    String, Float, Integer, Boolean, DateTime, Text, Enum, ForeignKey, Index,
)
from sqlalchemy.dialects.postgresql import UUID, JSONB, ARRAY
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column, relationship
import enum


class Base(DeclarativeBase):
    pass


class PositionType(str, enum.Enum):
    STOCK = "stock"
    OPTION = "option"
    SPREAD = "spread"
    FUTURE = "future"


class Direction(str, enum.Enum):
    LONG = "long"
    SHORT = "short"


class TradeStatus(str, enum.Enum):
    OPEN = "open"
    CLOSED = "closed"


class HoldingType(str, enum.Enum):
    CORE_HOLD = "core_hold"
    TACTICAL = "tactical"


class BetStatus(str, enum.Enum):
    WATCHING = "watching"
    ENTERED = "entered"
    PASSED = "passed"
    CLOSED = "closed"


class Trade(Base):
    __tablename__ = "trades"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=datetime.utcnow)

    # Metadata
    strategy_name: Mapped[str] = mapped_column(String(100))
    setup_classification: Mapped[str | None] = mapped_column(String(100))
    account: Mapped[str] = mapped_column(String(100))
    tags: Mapped[list | None] = mapped_column(ARRAY(String), default=list)

    # Entry snapshot (immutable after creation)
    entry_timestamp: Mapped[datetime] = mapped_column(DateTime(timezone=True))
    underlying_symbol: Mapped[str] = mapped_column(String(10), index=True)
    entry_price: Mapped[float] = mapped_column(Float)
    entry_iv: Mapped[float | None] = mapped_column(Float)
    iv_rank: Mapped[float | None] = mapped_column(Float)
    entry_volume: Mapped[int | None] = mapped_column(Integer)
    market_context: Mapped[str | None] = mapped_column(String(50))

    # Option fields (immutable)
    strike_price: Mapped[float | None] = mapped_column(Float)
    expiration_date: Mapped[datetime | None] = mapped_column(DateTime)
    premium: Mapped[float | None] = mapped_column(Float)
    bid_ask_spread: Mapped[float | None] = mapped_column(Float)
    open_interest: Mapped[int | None] = mapped_column(Integer)

    # Entry Greeks (immutable)
    entry_delta: Mapped[float | None] = mapped_column(Float)
    entry_gamma: Mapped[float | None] = mapped_column(Float)
    entry_theta: Mapped[float | None] = mapped_column(Float)
    entry_vega: Mapped[float | None] = mapped_column(Float)
    entry_rho: Mapped[float | None] = mapped_column(Float)

    # Position details
    position_type: Mapped[str] = mapped_column(Enum(PositionType, name="position_type_enum"))
    direction: Mapped[str] = mapped_column(Enum(Direction, name="direction_enum"))
    quantity: Mapped[int] = mapped_column(Integer)
    max_risk: Mapped[float | None] = mapped_column(Float)
    max_profit: Mapped[float | None] = mapped_column(Float)
    buying_power_used: Mapped[float | None] = mapped_column(Float)

    # Exit snapshot (set on close, immutable after)
    exit_timestamp: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    exit_price: Mapped[float | None] = mapped_column(Float)
    exit_premium: Mapped[float | None] = mapped_column(Float)
    exit_iv: Mapped[float | None] = mapped_column(Float)
    exit_delta: Mapped[float | None] = mapped_column(Float)
    exit_gamma: Mapped[float | None] = mapped_column(Float)
    exit_theta: Mapped[float | None] = mapped_column(Float)
    exit_vega: Mapped[float | None] = mapped_column(Float)

    # Performance (calculated on close)
    realized_pnl: Mapped[float | None] = mapped_column(Float)
    realized_pnl_pct: Mapped[float | None] = mapped_column(Float)
    risk_adjusted_return: Mapped[float | None] = mapped_column(Float)

    # Decision logging
    trade_thesis: Mapped[str] = mapped_column(Text)
    entry_rationale: Mapped[str] = mapped_column(Text)
    defined_edge: Mapped[str | None] = mapped_column(Text)
    invalidation_conditions: Mapped[str] = mapped_column(Text)
    exit_plan: Mapped[dict | None] = mapped_column(JSONB, default=dict)
    post_review: Mapped[dict | None] = mapped_column(JSONB)

    status: Mapped[str] = mapped_column(
        Enum(TradeStatus, name="trade_status_enum"), default=TradeStatus.OPEN
    )

    webull_account_id: Mapped[str | None] = mapped_column(String(64), nullable=True)
    webull_position_id: Mapped[str | None] = mapped_column(String(80), nullable=True)

    snapshots: Mapped[list["TimeSeriesSnapshot"]] = relationship(
        back_populates="trade", cascade="all, delete-orphan", order_by="TimeSeriesSnapshot.timestamp"
    )

    __table_args__ = (
        Index("ix_trades_strategy", "strategy_name"),
        Index("ix_trades_status", "status"),
        Index("ix_trades_entry_ts", "entry_timestamp"),
        Index("ix_trades_webull", "webull_account_id", "webull_position_id"),
    )


class TimeSeriesSnapshot(Base):
    __tablename__ = "time_series_snapshots"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    trade_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("trades.id", ondelete="CASCADE"), index=True
    )
    timestamp: Mapped[datetime] = mapped_column(DateTime(timezone=True))
    underlying_price: Mapped[float] = mapped_column(Float)
    position_value: Mapped[float] = mapped_column(Float)
    delta: Mapped[float | None] = mapped_column(Float)
    gamma: Mapped[float | None] = mapped_column(Float)
    theta: Mapped[float | None] = mapped_column(Float)
    vega: Mapped[float | None] = mapped_column(Float)
    iv: Mapped[float | None] = mapped_column(Float)

    trade: Mapped["Trade"] = relationship(back_populates="snapshots")

    __table_args__ = (
        Index("ix_snapshots_trade_ts", "trade_id", "timestamp"),
    )


class Position(Base):
    """Long-term position tracker (core holds like TSLA, PLTR)."""
    __tablename__ = "positions"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    symbol: Mapped[str] = mapped_column(String(10), unique=True, index=True)
    quantity: Mapped[float] = mapped_column(Float)
    avg_cost: Mapped[float] = mapped_column(Float)
    current_value: Mapped[float | None] = mapped_column(Float)
    unrealized_pnl: Mapped[float | None] = mapped_column(Float)
    position_type: Mapped[str] = mapped_column(
        Enum(HoldingType, name="holding_type_enum"), default=HoldingType.CORE_HOLD
    )
    notes: Mapped[str | None] = mapped_column(Text)
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=datetime.utcnow, onupdate=datetime.utcnow
    )


class MarketDataCache(Base):
    __tablename__ = "market_data_cache"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    symbol: Mapped[str] = mapped_column(String(10), index=True)
    data_type: Mapped[str] = mapped_column(String(20))
    data: Mapped[dict] = mapped_column(JSONB)
    fetched_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=datetime.utcnow)

    __table_args__ = (
        Index("ix_mdc_symbol_type", "symbol", "data_type"),
    )


class WsbSentiment(Base):
    __tablename__ = "wsb_sentiment"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    symbol: Mapped[str] = mapped_column(String(10), index=True)
    mention_count: Mapped[int] = mapped_column(Integer)
    avg_sentiment: Mapped[float] = mapped_column(Float)
    top_posts: Mapped[dict | None] = mapped_column(JSONB)
    scraped_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=datetime.utcnow)
    is_spike: Mapped[bool] = mapped_column(Boolean, default=False)
    source: Mapped[str] = mapped_column(String(20), default="apewisdom")

    __table_args__ = (
        Index("ix_wsb_symbol_scraped", "symbol", "scraped_at"),
    )


class AiInsightLog(Base):
    __tablename__ = "ai_insight_logs"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    insight_type: Mapped[str] = mapped_column(String(50))
    content: Mapped[str] = mapped_column(Text)
    related_symbols: Mapped[list | None] = mapped_column(ARRAY(String))
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=datetime.utcnow)


class Bet(Base):
    """WSB-sourced speculative opportunities -- separate from core strategies."""
    __tablename__ = "bets"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    symbol: Mapped[str] = mapped_column(String(10), index=True)
    source_post_ids: Mapped[list | None] = mapped_column(ARRAY(String))
    sentiment_score: Mapped[float] = mapped_column(Float)
    mention_velocity: Mapped[float | None] = mapped_column(Float)
    status: Mapped[str] = mapped_column(
        Enum(BetStatus, name="bet_status_enum"), default=BetStatus.WATCHING
    )
    notes: Mapped[str | None] = mapped_column(Text)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=datetime.utcnow)
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=datetime.utcnow, onupdate=datetime.utcnow
    )
