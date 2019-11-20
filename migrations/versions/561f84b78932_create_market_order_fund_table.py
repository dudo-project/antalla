"""create market order fund table

Revision ID: 561f84b78932
Revises: 76f4db23257a
Create Date: 2019-09-22 01:22:24.172564

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = '561f84b78932'
down_revision = '76f4db23257a'
branch_labels = None
depends_on = None


def upgrade():
    op.create_table(
        "market_order_funds",
        sa.Column("id", sa.Integer, primary_key=True),
        sa.Column("timestamp", sa.DateTime, nullable=False),
        sa.Column("funds", sa.Float, nullable=False),
    )


def downgrade():
    op.drop_table("market_order_funds")
