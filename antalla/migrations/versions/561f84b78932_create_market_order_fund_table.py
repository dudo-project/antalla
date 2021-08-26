"""create market order fund table

Revision ID: 561f84b78932
Revises: 76f4db23257a
Create Date: 2019-09-22 01:22:24.172564

"""
from antalla.settings import TABLE_PREFIX
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = "561f84b78932"
down_revision = "76f4db23257a"
branch_labels = None
depends_on = None


def upgrade():
    op.create_table(
        TABLE_PREFIX + "market_order_funds",
        sa.Column("id", sa.Integer, primary_key=True),
        sa.Column("timestamp", sa.DateTime, nullable=False),
        sa.Column("funds", sa.Float, nullable=False),
        sa.Column(
            "exchange_id",
            sa.Integer,
            sa.ForeignKey(TABLE_PREFIX + "exchanges.id"),
            nullable=False,
        ),
        sa.Column("exchange_order_id", sa.String, nullable=False),
        sa.ForeignKeyConstraint(
            ["exchange_id", "exchange_order_id"],
            [
                TABLE_PREFIX + "orders.exchange_id",
                TABLE_PREFIX + "orders.exchange_order_id",
            ],
        ),
        sa.Index(
            "market_order_funds-exchange-id-exchange-order-id-idx",
            "exchange_id",
            "exchange_order_id",
        ),
    )


def downgrade():
    op.drop_table(TABLE_PREFIX + "market_order_funds")
