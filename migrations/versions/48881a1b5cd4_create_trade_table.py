"""create trade table

Revision ID: 48881a1b5cd4
Revises: 4070698d0213
Create Date: 2019-09-22 01:25:31.892912

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = '48881a1b5cd4'
down_revision = '4070698d0213'
branch_labels = None
depends_on = None


def upgrade():
     op.create_table(
        "trades",
        sa.Column("exchange_trade_id ", sa.String, primary_key=True),
        sa.Column("exchange_id ", sa.Integer, sa.ForeignKey("exchanges.id"), nullable=False, primary_key=True),
        sa.Column("timestamp ", sa.DateTime, nullable=False, index=True),
        sa.Column("trade_type ", sa.String),
        sa.Column("buy_sym_id ", sa.String, sa.ForeignKey("coins.symbol"), nullable=False, index=True),
        sa.Column("sell_sym_id ", sa.String, sa.ForeignKey("coins.symbol"), nullable=False, index=True),
        sa.Column("maker ", sa.String),
        sa.Column("taker ", sa.String),
        sa.Column("price ", sa.Float, nullable=False),
        sa.Column("size ", sa.Float, nullable=False),
        sa.Column("total ", sa.Float),
        sa.Column("buyer_fee ", sa.Float),
        sa.Column("seller_fee ", sa.Float),
        sa.Column("gas_fee ", sa.Float),
        sa.Column("exchange_order_id ", sa.String, index=True),
        sa.Column("maker_order_id ", sa.String, index=True),
        sa.Column("taker_order_id ", sa.String, index=True),
    )


def downgrade():
    op.drop_table("trades")
