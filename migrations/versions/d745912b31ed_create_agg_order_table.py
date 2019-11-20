"""create agg order table

Revision ID: d745912b31ed
Revises: 48881a1b5cd4
Create Date: 2019-09-22 01:27:35.584387

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = 'd745912b31ed'
down_revision = '48881a1b5cd4'
branch_labels = None
depends_on = None


def upgrade():
    op.create_table(
        "aggregate_orders",
        sa.Column("hash_id", sa.String, primary_key=True),
        sa.Column("last_update_id", sa.Integer),
        sa.Column("timestamp", sa.DateTime, index=True, nullable=False),
        sa.Column("buy_sym_id", sa.String, sa.ForeignKey("coins.symbol"), nullable=False, index=True),
        sa.Column("sell_sym_id", sa.String, sa.ForeignKey("coins.symbol"), nullable=False, index=True),
        sa.Column("exchange_id", sa.Integer, sa.ForeignKey("exchanges.id"), nullable=False, index=True),
        sa.Column("order_type", sa.String, nullable=False),
        sa.Column("price", sa.Float, nullable=False, index=True),
        sa.Column("size", sa.Float, nullable=False),
    )


def downgrade():
    op.drop_table("aggregate_orders")
