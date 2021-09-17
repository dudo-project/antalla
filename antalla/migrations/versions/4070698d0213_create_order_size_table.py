"""create order size table

Revision ID: 4070698d0213
Revises: 561f84b78932
Create Date: 2019-09-22 01:24:09.740674

"""
from antalla.settings import TABLE_PREFIX
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = "4070698d0213"
down_revision = "561f84b78932"
branch_labels = None
depends_on = None


def upgrade():
    op.create_table(
        TABLE_PREFIX + "order_sizes",
        sa.Column("id", sa.Integer, primary_key=True),
        sa.Column("timestamp", sa.DateTime, nullable=False),
        sa.Column("size", sa.Float, nullable=False),
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
            "order_sizes-exchange-id-exchange-order-id-idx",
            "exchange_id",
            "exchange_order_id",
        ),
    )


def downgrade():
    op.drop_table(TABLE_PREFIX + "order_sizes")
