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
        raw_ob = self._get_ob(buy_sym_id, sell_sym_id, exchange)
        order_history = self._parse_ob(raw_ob)
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
        plt.show()
        #plt.savefig("hitbtc_depth.png")

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
        
    def _get_ob(self, buy_sym_id, sell_sym_id, exchange):
        """ queries the database for the latest orderbook for the given pair
        - for visualisation purposes not all orders are retrieved
        - orders are only retrieved if ask/bid prices lie below/above the median price, respectively
        """

        query = (
        """
        select 
            exchanges.name,
            timestamp,
            buy_sym_id,
            sell_sym_id,
            order_type,
            price,
            size
        from aggregate_orders inner join exchanges on exchanges.name = '""" + exchange.lower() + "'" +
        " and buy_sym_id = '" + buy_sym_id.upper() + "' and sell_sym_id = '" + sell_sym_id.upper() + "'" +
        """
        and ((aggregate_orders.order_type = 'bid' and aggregate_orders.price >= (
            select percentile_disc(0.25) within group (order by price)
            from aggregate_orders
            where order_type = 'bid'
            ))
        or (aggregate_orders.order_type = 'ask' and aggregate_orders.price <= (
            select percentile_disc(0.5) within group (order by price)
            from aggregate_orders
            where order_type = 'ask'
                ))) order by timestamp asc
        """
        )
        return session.execute(query)
    
    def _parse_ob(self, raw_ob):
        ob = []
        for order in list(raw_ob):
            ob.append(dict(
                timestamp=order[1],
                type=order[4],
                price=float(order[5]),
                size=float(order[6])
            ))
        return ob

"""
TODO: implement stats tracker for snapshot of order book:
    -spread
    -mid price
    -sum of bids
    -sum of asks
    -number of bids
    -number of asks
    -normalise in USD (?) 

The OrderbookAnalyser allows for a visualisation of the current order book (using data after 2019-04-28).

Note: the implementation can still be improved performance-wise. 
Example:
    > oba = OrderBookAnalyser()
    > oba.visualise_ob("ETH", "BTC", "binance")
"""

oba = OrderBookAnalyser()
oba.visualise_ob("ETH", "BTC", "hitbtc")
