
from datetime import datetime
import logging

from .db import session
from . import models
from . import actions

SNAPSHOT_INTERVAL_SECONDS = 1

class OBSnapshotGenerator:
    def __init__(self, exchanges):
        self.exchanges = exchanges

    def run(self):
        # generate snapshots every S seconds for T orders for time t > last snapshot timestamp
       """
        with order_book as (
        with latest_orders as (
        select order_type, price, max(last_update_id) max_update_id
        from aggregate_orders
        where timestamp <= '2019-05-13 18:57:42'
        group by aggregate_orders.price,
                    aggregate_orders.order_type)
        select aggregate_orders.id,
            order_type,
            price,
            size,
            last_update_id,
            timestamp,
            name,
            buy_sym_id,
            sell_sym_id
        from aggregate_orders
                inner join exchanges on aggregate_orders.exchange_id = exchanges.id
        where (order_type, price, last_update_id) in (select * from latest_orders)
        and size > 0
        and buy_sym_id = 'ETH'
        and sell_sym_id = 'BTC'
        and name = 'hitbtc'
        and timestamp <= '2019-05-13 18:57:42'
        )
        select *, true as is_quartile
        from order_book where (order_book.order_type = 'bid' and order_book.price >= (
            select percentile_disc(0.75) within group (order by order_book.price)
            from order_book
                where order_book.order_type = 'bid'
        )) or (order_book.order_type = 'ask' and order_book.price <= (
            select percentile_disc(0.25) within group (order by order_book.price)
            from order_book
                where order_book.order_type = 'ask'
        ))
        union all
        select *, false as is_quartile from order_book
        order by timestamp desc
        """