"""create coin table

Revision ID: b97a89b20fa2
Revises: 
Create Date: 2019-09-21 02:14:03.713556

"""
from antalla.settings import TABLE_PREFIX
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = "b97a89b20fa2"
down_revision = None
branch_labels = None
depends_on = None


def upgrade():
    op.create_table(
        TABLE_PREFIX + "coins",
        sa.Column("symbol", sa.String, primary_key=True),
        sa.Column("name", sa.String),
        sa.Column("price_usd", sa.Float),
        sa.Column("last_price_updated", sa.DateTime),
    )


def downgrade():
    op.drop_table(TABLE_PREFIX + "coins")
