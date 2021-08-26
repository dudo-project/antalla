from antalla import models
import logging
import re

import seaborn as sns
import matplotlib.pyplot as plt

from antalla.db import session


sns.set_style("darkgrid")


class OrderBookAnalyser:
    def __init__(self, buy_sym_id, sell_sym_id, exchange):
        self.running = True
        self.exchange = exchange
        self.buy_sym_id, self.sell_sym_id = self._get_original_market(
            buy_sym_id, sell_sym_id
        )

    def _get_original_market(self, buy_sym_id, sell_sym_id):
        if buy_sym_id > sell_sym_id:
            temp = buy_sym_id
            buy_sym_id = sell_sym_id
            sell_sym_id = temp
        original_market_result = list(
            session.execute(
                f"""
        select original_name from {models.ExchangeMarket.__tablename__} em
        inner join exchanges e on em.exchange_id = e.id
        where e.name = :exchange and first_coin_id= :buy_sym_id and second_coin_id= :sell_sym_id
        """,
                {
                    "exchange": self.exchange,
                    "buy_sym_id": buy_sym_id,
                    "sell_sym_id": sell_sym_id,
                },
            )
        )
        if not len(original_market_result):
            self.running = False
            logging.info(
                "No market '{}-{}' registered for '{}'".format(
                    buy_sym_id, sell_sym_id, self.exchange
                )
            )
            return None, None
        else:
            original_market = re.split(
                "[_-]", (original_market_result[0]["original_name"])
            )
            if len(original_market) > 1:
                return original_market
            elif buy_sym_id + sell_sym_id == original_market[0]:
                return buy_sym_id, sell_sym_id
            else:
                return sell_sym_id, buy_sym_id

    def generate_depth_data(self):
        orders = dict(bid={}, ask={})
        result_proxy_ob = self._get_ob_mid_price()
        order_history = self._parse_ob(result_proxy_ob)
        for order in order_history:
            values = orders[order["type"]]
            if order["size"] == 0:
                values.pop(order["price"], None)
            else:
                values[order["price"]] = order["size"]

        stacked_bids = self._get_stacked_orders(
            orders["bid"], reversed(sorted(orders["bid"]))
        )
        if not stacked_bids:
            return dict(
                size=0,
                exchange=self.exchange,
                buy_sym=self.buy_sym_id,
                sell_sym=self.sell_sym_id,
            )
        buy_price, buy_qty = zip(*sorted(stacked_bids.items()))
        stacked_asks = self._get_stacked_orders(orders["ask"], sorted(orders["ask"]))
        sell_price, sell_qty = zip(*sorted(stacked_asks.items()))
        return dict(
            size=len(order_history),
            exchange=self.exchange,
            buy_sym=self.buy_sym_id,
            sell_sym=self.sell_sym_id,
            asks_sum=sum(orders["ask"]),
            bids_sum=sum(orders["bid"]),
            mean_bid_quantity=order_history[0]["mid_price"],
            buy_price=buy_price,
            buy_quantity=buy_qty,
            sell_price=sell_price,
            sell_quantity=sell_qty,
        )

    def visualise_ob(self):
        ob_data = self.generate_depth_data()
        logging.info(
            "order book size: %s - asks: %s - bids: %s",
            ob_data["size"],
            ob_data["asks_sum"],
            ob_data["bids_sum"],
        )
        plt.title(
            self.exchange.capitalize()
            + " Order Book: "
            + self.buy_sym_id
            + "-"
            + self.sell_sym_id
        )
        plt.plot(ob_data["buy_price"], ob_data["buy_quantity"], label="Bids")
        plt.plot(ob_data["sell_price"], ob_data["sell_quantity"], label="Asks")
        plt.xlabel("Price Level (" + self.sell_sym_id + ")")
        plt.ylabel("Quantity")
        plt.fill_between(ob_data["buy_price"], ob_data["buy_quantity"], alpha=0.3)
        plt.fill_between(ob_data["sell_price"], ob_data["sell_quantity"], alpha=0.3)
        # plots the mid price
        # mid_price = ob_data["mean_bid_quantity"]
        # mean_bid_qty = np.mean(ob_data["buy_quantity"])
        # plt.plot((mid_price, mid_price), (0, 0.5*(mean_bid_qty)))
        # plt.text(mid_price, (mean_bid_qty + (0.075*mean_bid_qty)), "mid price: "+str(mid_price), fontsize=16)
        plt.pause(0.05)
        plt.clf()

    def _get_stacked_orders(self, orders, keys):
        # """ returns a dict containing stacked order quantities
        # >>> orders = dict(0.4=10, 0.5=20, 0.6=30, 0.8=15)
        # >>> OrderBookAnalyser._get_stacked_orders(dummy_self, orders, orders.keys())
        # {0.4:10, 0.5:30, 0.6:60, 0.8:75}
        # """
        stacked_orders = {}
        stacked_qty = 0.0
        for pl in keys:
            stacked_qty += float(orders[pl])
            stacked_orders[pl] = stacked_qty
        return stacked_orders

    def _get_ob_quartiles(self):
        query = f"""
        with order_book as (
                  with latest_orders as (
                      select order_type, price, max(last_update_id) max_update_id
                      from {models.AggOrder.__tablename__} ag
                      group by ag.price, ag.order_type)
                  select order_type,
                         price,
                         size,
                         last_update_id,
                         timestamp,
                         name,
                         buy_sym_id,
                         sell_sym_id
                  from {models.AggOrder.__tablename__} ag
                           inner join {models.Exchange.__tablename__} e on ag.exchange_id = e.id
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
        return session.execute(
            query,
            {
                "buy_sym_id": self.buy_sym_id.upper(),
                "sell_sym_id": self.sell_sym_id.upper(),
                "exchange": self.exchange.lower(),
            },
        )

    def _get_ob_mid_price(self):
        """queries the database for the latest orderbook for the given pair
        - for visualisation purposes not all orders are retrieved
        - orders are only retrieved if ask/bid prices lie below/above the median price, respectively
        """
        query = f"""
        with order_book as (
            with latest_orders as (
                select order_type, price, max(last_update_id) max_update_id, exchange_id
                from {models.AggOrder.__tablename__} ag
                group by ag.price, ag.order_type, ag.exchange_id)
            select order_type,
                price,
                buy_sym_id,
                size,
                last_update_id,
                timestamp,
                name,
                sell_sym_id
            from {models.AggOrder.__tablename__} ag
                    inner join {models.Exchange.__tablename__} e on ag.exchange_id = e.id
            where (order_type, price, last_update_id, exchange_id) in (select * from latest_orders)
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
        select order_type, price, size, timestamp, max_bid, min_ask, mid
        from order_book, mid_price
        where (order_book.order_type = 'bid' and order_book.price >= 0.99 * mid_price.mid)
        or (order_book.order_type = 'ask' and order_book.price <= 1.01 * mid_price.mid) order by timestamp desc
        """
        return session.execute(
            query,
            {
                "buy_sym_id": self.buy_sym_id.upper(),
                "sell_sym_id": self.sell_sym_id.upper(),
                "exchange": self.exchange.lower(),
            },
        )

    def _parse_ob(self, raw_ob):
        ob = []
        for order in list(raw_ob):
            ob.append(
                dict(
                    timestamp=order["timestamp"],
                    type=order["order_type"],
                    price=float(order["price"]),
                    size=float(order["size"]),
                    mid_price=float(order["mid"]),
                )
            )
        return ob
