"""create exchange market table

Revision ID: 76f253d77eba
Revises: 4d9ca085df42
Create Date: 2019-09-22 01:32:11.855978

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = '76f253d77eba'
down_revision = '4d9ca085df42'
branch_labels = None
depends_on = None


def upgrade():
    op.create_table(
        "exchange_markets",
        sa.Column("volume_usd", sa.Float),
        sa.Column("quoted_volume", sa.Float, nullable=False),
        sa.Column("quoted_vol_timestamp", sa.DateTime),
        sa.Column("vol_usd_timestamp", sa.DateTime),
        sa.Column("agg_orders_count", sa.Integer, server_default="0", nullable=False),
        sa.Column("quoted_volume_id", sa.String, sa.ForeignKey("coins.symbol"), nullable=False),
        sa.Column("original_name", sa.String, nullable=False),
        sa.Column("first_coin_id", sa.String, sa.ForeignKey("coins.symbol"), nullable=False, index=True),
        sa.Column("second_coin_id", sa.String, sa.ForeignKey("coins.symbol"), nullable=False, index=True),
        sa.Column("exchange_id", sa.Integer, sa.ForeignKey("exchanges.id"), nullable=False, index=True),
        sa.PrimaryKeyConstraint("first_coin_id", "second_coin_id", "exchange_id"),
        sa.ForeignKeyConstraint(
            ["first_coin_id", "second_coin_id"],
            ["markets.first_coin_id", "markets.second_coin_id"],
        ),
        sa.Index("exchange-market-fk-idx", "first_coin_id", "second_coin_id"),
        sa.Index("exchange-market-fk-full-idx", "first_coin_id", "second_coin_id", "exchange_id"),
        sa.Index("exchange-market-agg_orders_count_idx", "agg_orders_count"),
    )


def downgrade():
    op.drop_table("exchange_markets")
