"""create exchange table

Revision ID: bfa53193d3bf
Revises: b97a89b20fa2
Create Date: 2019-09-22 01:17:06.735174

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = 'bfa53193d3bf'
down_revision = 'b97a89b20fa2'
branch_labels = None
depends_on = None


def upgrade():
    op.create_table(
        "exchanges",
        sa.Column("id", sa.Integer, primary_key=True),
        sa.Column("name", sa.String),
    )


def downgrade():
    op.drop_table("exchanges")
