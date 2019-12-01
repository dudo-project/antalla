"""create order book snapshot table

Revision ID: ca6cd71568db
Revises: 76f253d77eba
Create Date: 2019-09-22 01:33:59.794177

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = 'ca6cd71568db'
down_revision = '76f253d77eba'
branch_labels = None
depends_on = None


def upgrade():
    op.create_table(
        "order_book_snapshots",
        sa.Column("timestamp", sa.DateTime, nullable=False, primary_key=True),
        sa.Column("snapshot_type", sa.String, nullable=False, primary_key=True),
        sa.Column("mid_price_range", sa.Float, nullable=False, primary_key=True),
        sa.Column("buy_sym_id", sa.String, sa.ForeignKey("coins.symbol"), nullable=False, index=True, primary_key=True),
        sa.Column("sell_sym_id", sa.String, sa.ForeignKey("coins.symbol"), nullable=False, index=True, primary_key=True),
        sa.Column("exchange_id", sa.Integer, sa.ForeignKey("exchanges.id"), nullable=False, index=True, primary_key=True),
        sa.Column("spread", sa.Float, nullable=False, index=True),
        sa.Column("bids_volume", sa.Float, nullable=False),
        sa.Column("asks_volume", sa.Float, nullable=False),
        sa.Column("bids_count", sa.Integer, nullable=False),
        sa.Column("asks_count", sa.Integer, nullable=False),
        sa.Column("bids_price_stddev", sa.Float, nullable=False),
        sa.Column("asks_price_stddev", sa.Float, nullable=False),
        sa.Column("bids_price_mean", sa.Float, nullable=False),
        sa.Column("asks_price_mean", sa.Float, nullable=False),
        sa.Column("min_ask_price", sa.Float, nullable=False),
        sa.Column("min_ask_size", sa.Float, nullable=False),
        sa.Column("max_bid_price", sa.Float, nullable=False),
        sa.Column("max_bid_size", sa.Float, nullable=False),
        sa.Column("bid_price_median", sa.Float, nullable=False),
        sa.Column("ask_price_median", sa.Float, nullable=False),
    )


def downgrade():
    op.drop_table("order_book_snapshots")
