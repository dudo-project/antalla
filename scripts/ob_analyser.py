import time
import sys
import numpy as np
import pandas as pd
import seaborn as sns
import matplotlib
import matplotlib.pyplot as plt
from matplotlib.dates import DateFormatter 
from matplotlib.ticker import PercentFormatter
import matplotlib.style as style

from antalla.db import session
from antalla import models

sns.set_style("darkgrid")

class OrderBookAnalyser:
    def visualise_ob(self, buy_sym_id, sell_sym_id, exchange):
        ob_bids = dict()
        ob_asks = dict()
        result_proxy_ob = self._get_ob_mid_price(buy_sym_id, sell_sym_id, exchange)
        order_history = self._parse_ob(result_proxy_ob)
        print("orderbook size: ", len(order_history))
        for order in order_history:
            if order["type"] == "bid":
                if order["size"] == 0:
                    ob_bids.pop(order["price"], None)
                else:
                    ob_bids[order["price"]] = order["size"]
            elif order["type"] == "ask":
                if order["size"] == 0:
                    ob_asks.pop(order["price"], None)
                else:
                    ob_asks[order["price"]] = order["size"]

        stacked_bids = self._get_stacked_orders(ob_bids, reversed(sorted(ob_bids)))
        buy_price, buy_qty = zip(*sorted(stacked_bids.items()))
        stacked_asks = self._get_stacked_orders(ob_asks, sorted(ob_asks))
        sell_price, sell_qty = zip(*sorted(stacked_asks.items()))

        plt.title(exchange.capitalize() + " Order Book: " + buy_sym_id + "-" + sell_sym_id)
        plt.plot(buy_price, buy_qty, label="Bids")
        plt.plot(sell_price, sell_qty, label="Asks")
        plt.xlabel("Price Level (" + sell_sym_id + ")")
        plt.ylabel("Quantity")
        plt.fill_between(buy_price, buy_qty, alpha=0.3)
        plt.fill_between(sell_price, sell_qty, alpha=0.3)
        #plt.show()
        plt.pause(0.05)
        plt.clf()
        #plt.savefig("order_book_depth.png")

    def _get_stacked_orders(self, orders, keys):
        """ returns a dict containing stacked order quantities
        >>> orders = dict(0.4=10, 0.5=20, 0.6=30, 0.8=15)
        >>> OrderBookAnalyser._get_stacked_orders(dummy_self, orders, orders.keys())
        {0.4:10, 0.5:30, 0.6:60, 0.8:75}
        """

        stacked_orders = {}
        stacked_qty = 0.0
        for pl in keys:
            stacked_qty += float(orders[pl])
            stacked_orders[pl] = stacked_qty
        return stacked_orders
        
    def _get_ob_quartiles(self, buy_sym_id, sell_sym_id, exchange):
        query = (
        """
        with order_book as (
                  with latest_orders as (
                      select order_type, price, max(last_update_id) max_update_id
                      from aggregate_orders
                      group by aggregate_orders.price, aggregate_orders.order_type)
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
                    and buy_sym_id = :buy_sym_id
                    and sell_sym_id = :sell_sym_id
                    and name = :exchange
                  order by price asc
        ) select * from order_book where (order_book.order_type = 'bid' and order_book.price >= (
            select percentile_disc(0.75) within group (order by order_book.price)
            from order_book
                where order_book.order_type = 'bid'
        )
            ) or (order_book.order_type = 'ask' and order_book.price <= (
            select percentile_disc(0.25) within group (order by order_book.price)
            from order_book
                where order_book.order_type = 'ask'
        ))
        """
        )
        return session.execute(query, {"buy_sym_id": buy_sym_id.upper(), "sell_sym_id": sell_sym_id.upper(), "exchange": exchange.lower()})

    def _get_ob_mid_price(self, buy_sym_id, sell_sym_id, exchange):
        """ queries the database for the latest orderbook for the given pair
        - for visualisation purposes not all orders are retrieved
        - orders are only retrieved if ask/bid prices lie below/above the median price, respectively
        """
        query = (
        """
        with order_book as (
            with latest_orders as (
                select order_type, price, max(last_update_id) max_update_id
                from aggregate_orders
                group by aggregate_orders.price, aggregate_orders.order_type)
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
            and buy_sym_id = :buy_sym_id
            and sell_sym_id = :sell_sym_id
            and name = :exchange
            order by price asc
        ),
            mid_price as (
                with max_min_prices as (
                    with max_bid_price as (
                        select max(price) max_bid
                        from order_book
                        where (order_book.order_type = 'bid')
                    ),
                        min_ask_price as (
                            select min(price) min_ask
                            from order_book
                            where (order_book.order_type = 'ask')
                        )
                    select *
                    from max_bid_price,
                        min_ask_price)
                select ((max_min_prices.min_ask + max_min_prices.max_bid) / 2) mid, max_bid, min_ask
                from max_min_prices
            )
        select *
        from order_book, mid_price
        where (order_book.order_type = 'bid' and order_book.price >= 0.99 * mid_price.mid)
        or (order_book.order_type = 'ask' and order_book.price <= 1.01 * mid_price.mid);
        """
        )
        return session.execute(query, {"buy_sym_id": buy_sym_id.upper(), "sell_sym_id": sell_sym_id.upper(), "exchange": exchange.lower()})
    
    def _parse_ob(self, raw_ob):
        ob = []
        for order in list(raw_ob):
            ob.append(dict(
                timestamp=order[5],
                type=order[1],
                price=float(order[2]),
                size=float(order[3])
            ))
        return ob

"""
The OrderbookAnalyser allows for a visualisation of the current order book.

Note: the implementation can still be improved performance-wise. 
Example:
    > oba = OrderBookAnalyser()
    > oba.visualise_ob("ETH", "BTC", "binance")
"""

oba = OrderBookAnalyser()
while True:
    try:
        #oba.visualise_ob("ETH", "BTC", "coinbase")
        oba.visualise_ob("BTC", "USD", "coinbase")
    except KeyboardInterrupt:
        sys.exit()