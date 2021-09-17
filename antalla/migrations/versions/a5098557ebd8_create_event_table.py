"""create event table

Revision ID: a5098557ebd8
Revises: ca6cd71568db
Create Date: 2019-09-22 01:36:04.659315

"""
from antalla.settings import TABLE_PREFIX
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = "a5098557ebd8"
down_revision = "ca6cd71568db"
branch_labels = None
depends_on = None


def upgrade():
    op.create_table(
        TABLE_PREFIX + "events",
        sa.Column("id", sa.Integer, primary_key=True),
        sa.Column("session_id", sa.String, nullable=False, index=True),
        sa.Column("timestamp", sa.DateTime, nullable=False),
        sa.Column("connection_event", sa.String, nullable=False),
        sa.Column("data_collected", sa.String, nullable=False),
        sa.Column(
            "buy_sym_id",
            sa.String,
            sa.ForeignKey(TABLE_PREFIX + "coins.symbol"),
            nullable=False,
            index=True,
        ),
        sa.Column(
            "sell_sym_id",
            sa.String,
            sa.ForeignKey(TABLE_PREFIX + "coins.symbol"),
            nullable=False,
            index=True,
        ),
        sa.Column(
            "exchange_id",
            sa.Integer,
            sa.ForeignKey(TABLE_PREFIX + "exchanges.id"),
            nullable=False,
            index=True,
        ),
    )


def downgrade():
    op.drop_table(TABLE_PREFIX + "events")
