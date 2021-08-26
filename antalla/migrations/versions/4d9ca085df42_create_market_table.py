"""create market table

Revision ID: 4d9ca085df42
Revises: d745912b31ed
Create Date: 2019-09-22 01:30:28.375144

"""
from antalla.settings import TABLE_PREFIX
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = "4d9ca085df42"
# down_revision = 'd745912b31ed'
down_revision = "bfa53193d3bf"
branch_labels = None
depends_on = None


def upgrade():
    op.create_table(
        TABLE_PREFIX + "markets",
        sa.Column(
            "first_coin_id",
            sa.String,
            sa.ForeignKey(TABLE_PREFIX + "coins.symbol"),
            nullable=False,
            index=True,
            primary_key=True,
        ),
        sa.Column(
            "second_coin_id",
            sa.String,
            sa.ForeignKey(TABLE_PREFIX + "coins.symbol"),
            nullable=False,
            index=True,
            primary_key=True,
        ),
    )


def downgrade():
    op.drop_table(TABLE_PREFIX + "markets")
