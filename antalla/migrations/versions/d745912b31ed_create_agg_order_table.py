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
        sa.Column("first_coin_id", sa.String, sa.ForeignKey("coins.symbol"), nullable=False, index=True),
        sa.Column("second_coin_id", sa.String, sa.ForeignKey("coins.symbol"), nullable=False, index=True),
        sa.Column("exchange_id", sa.Integer, sa.ForeignKey("exchanges.id"), nullable=False, index=True),
        sa.Column("order_type", sa.String, nullable=False),
        sa.Column("price", sa.Float, nullable=False, index=True),
        sa.Column("size", sa.Float, nullable=False),
        sa.Index("latest_orders_index",
            "order_type", "price", "last_update_id", "exchange_id", unique=True),
        sa.Index("market_orders_index", "first_coin_id", "second_coin_id", "exchange_id"),
    )
    op.execute("""
    CREATE OR REPLACE FUNCTION update_agg_orders_count()
    RETURNS TRIGGER AS $$
    BEGIN
        UPDATE exchange_markets e
        SET agg_orders_count = agg_orders_count + 1
        WHERE e.first_coin_id = NEW.first_coin_id AND
            e.second_coin_id = NEW.second_coin_id AND
            e.exchange_id = NEW.exchange_id;
        RETURN NEW;
    END;
    $$ language plpgsql;
    """)
    op.execute("""
    CREATE TRIGGER update_exchange_markets_agg_orders_count
    AFTER INSERT ON aggregate_orders
    FOR EACH ROW
    EXECUTE PROCEDURE update_agg_orders_count();
    """)


def downgrade():
    op.drop_table("aggregate_orders")
