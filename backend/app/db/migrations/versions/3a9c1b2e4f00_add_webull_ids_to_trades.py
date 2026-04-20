"""add webull ids to trades

Revision ID: 3a9c1b2e4f00
Revises: 250cfe2984d0
Create Date: 2026-04-20 14:00:00.000000
"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


revision: str = "3a9c1b2e4f00"
down_revision: Union[str, None] = "250cfe2984d0"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.add_column(
        "trades",
        sa.Column("webull_account_id", sa.String(length=64), nullable=True),
    )
    op.add_column(
        "trades",
        sa.Column("webull_position_id", sa.String(length=80), nullable=True),
    )
    op.create_index(
        "ix_trades_webull",
        "trades",
        ["webull_account_id", "webull_position_id"],
        unique=False,
    )


def downgrade() -> None:
    op.drop_index("ix_trades_webull", table_name="trades")
    op.drop_column("trades", "webull_position_id")
    op.drop_column("trades", "webull_account_id")
