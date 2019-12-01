"""create order table

Revision ID: 76f4db23257a
Revises: bfa53193d3bf
Create Date: 2019-09-22 01:19:40.736314

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = '76f4db23257a'
down_revision = 'bfa53193d3bf'
branch_labels = None
depends_on = None


def upgrade():
    op.create_table(
        "orders",
        sa.Column("exchange_id", sa.Integer, sa.ForeignKey("exchanges.id"), primary_key=True),
        sa.Column("exchange_order_id", sa.String, primary_key=True),
        sa.Column("timestamp", sa.DateTime, index=True),
        sa.Column("filled_at", sa.DateTime),
        sa.Column("expiry", sa.DateTime),
        sa.Column("cancelled_at", sa.DateTime, index=True),
        sa.Column("buy_sym_id", sa.String, sa.ForeignKey("coins.symbol"), nullable=False, index=True),
        sa.Column("sell_sym_id", sa.String, sa.ForeignKey("coins.symbol"), nullable=False, index=True),
        sa.Column("gas_fee", sa.Float) ,
        sa.Column("user", sa.String),
        sa.Column("side", sa.String),
        sa.Column("price", sa.Float, nullable=False),
        sa.Column("last_updated", sa.DateTime),
        sa.Column("order_type", sa.String),
    )


def downgrade():
    op.drop_table("orders")
