from datetime import datetime
from datetime import timedelta
from collections import defaultdict

import numpy as np
import logging

from . import db
from . import models
from . import actions

SNAPSHOT_INTERVAL_SECONDS = 1
DEFAULT_COMMIT_INTERVAL = 100


class OBSnapshotGenerator:
    def __init__(
        self,
        exchanges,
        timestamp,
        mid_price_range=None,
        snapshot_interval=SNAPSHOT_INTERVAL_SECONDS,
        session=db.session,
        commit_interval=DEFAULT_COMMIT_INTERVAL,
    ):
        self.exchanges = exchanges
        self.stop_time = timestamp
        self.commit_interval = commit_interval
        self.snapshot_interval = snapshot_interval
        self.actions_buffer = []
        self.commit_counter = 0
        self.session = session
        self.mid_price_range = mid_price_range
        if self.mid_price_range:
            self._query_order_book = self._query_order_book_mid_price
        else:
            self.mid_price_range = 0
            self._query_order_book = self._query_order_book_quartile

    def _get_connection_window(self, last_update, key):
        connect_time = None
        disconnect_time = self.stop_time
        for con in self.event_log[key]:
            if last_update is not None:
                # if con["connection_event"] == "connect" and con["timestamp"] <= last_update:
                if con["connection_event"] == "connect":
                    connect_time = con["timestamp"]
                elif (
                    con["connection_event"] == "disconnect"
                    and con["timestamp"] > last_update
                ):
                    disconnect_time = con["timestamp"]
                    break
            else:
                if connect_time is None and con["connection_event"] == "connect":
                    connect_time = con["timestamp"]
                elif (
                    connect_time is not None and con["connection_event"] == "disconnect"
                ):
                    disconnect_time = con["timestamp"]
        return connect_time, disconnect_time

    def run(self):
        exchange_markets = self._query_exchange_markets()
        parsed_exchange_markets = self._parse_exchange_markets(exchange_markets)
        connection_events = self._query_connection_events()
        self._parse_connection_events(connection_events)
        for exchange in parsed_exchange_markets:
            snapshot_times = self._query_latest_snapshot(exchange)
            parsed_snapshot_times = self._parse_snapshot_times(snapshot_times)
            for market in parsed_exchange_markets[exchange]:
                market_key = exchange + market["buy_sym_id"] + market["sell_sym_id"]
                last_update_time = self._get_last_update_time(
                    market_key, parsed_snapshot_times
                )
                logging.debug("last snapshot update: {}".format(last_update_time))
                connect_time, disconnect_time = self._get_connection_window(
                    last_update_time, market_key
                )
                logging.info(
                    "order book snapshot - {} - '{}-{}'".format(
                        exchange.upper(), market["buy_sym_id"], market["sell_sym_id"]
                    )
                )
                logging.debug(
                    "snapshot window - start time: {} - end time: {}".format(
                        connect_time, disconnect_time
                    )
                )
                self._generate_all_snapshots(
                    connect_time, disconnect_time, last_update_time, market, exchange
                )
        if len(self.actions_buffer) > 0:
            self.session.commit()
            self.commit_counter += 1
        logging.info(
            "completed order book snapshots - total commits: {}".format(
                self.commit_counter
            )
        )

    def _generate_all_snapshots(
        self, connect_time, disconnect_time, snapshot_time, market, exchange
    ):
        """call the snapshot generator method for order book states following a prespecified interval (seconds).
        Order book snapshots are only made for time periods where there has been an active connection and orders have been received,
        i.e., no snapshot is created for a period where there is no connection to an exchange. Order book snapshots are always constructed
        for the range bteween the last successful exchange connection and the 'snapshot_time', which increases by the interval amount until
        the next time of a disconnection or the final stopping time is met.
        """
        market_key = exchange + market["buy_sym_id"] + market["sell_sym_id"]
        if snapshot_time is not None:
            snapshot_time += timedelta(seconds=self.snapshot_interval)
        else:
            snapshot_time = connect_time + timedelta(seconds=self.snapshot_interval)
        logging.debug(
            "initial times - current snapshot: {} - connect: {} - disconnect: {}".format(
                snapshot_time, connect_time, disconnect_time
            )
        )
        while snapshot_time < self.stop_time:
            start_time = datetime.strftime(connect_time, "%Y-%m-%d %H:%M:%S.%f")
            stop_time = datetime.strftime(snapshot_time, "%Y-%m-%d %H:%M:%S.%f")
            logging.debug("start: {}, end: {}".format(connect_time, snapshot_time))
            order_book = self._query_order_book(
                exchange,
                market["buy_sym_id"],
                market["sell_sym_id"],
                start_time,
                stop_time,
            )
            full_ob = self._parse_order_book(order_book)
            if full_ob is None:
                snapshot_time += timedelta(seconds=self.snapshot_interval)
                continue
            metadata = dict(
                timestamp=snapshot_time,
                exchange_id=market["exchange_id"],
                buy_sym_id=market["buy_sym_id"],
                sell_sym_id=market["sell_sym_id"],
            )
            snapshot = self._generate_snapshot(full_ob, metadata)
            action = actions.InsertAction([snapshot])
            action.execute(self.session)
            if len(self.actions_buffer) >= self.commit_interval:
                self.session.commit()
                self.commit_counter += 1
                logging.debug(
                    " {}-{} - order book snapshot commit[{}]".format(
                        market["buy_sym_id"], market["sell_sym_id"], self.commit_counter
                    )
                )
            else:
                self.actions_buffer.append(action)
            logging.debug("order book snapshot created - {}".format(snapshot_time))
            snapshot_time += timedelta(seconds=self.snapshot_interval)
            if snapshot_time >= disconnect_time:
                snapshot_time, disconnect_time = self._get_connection_window(
                    snapshot_time, market_key
                )
                connect_time = snapshot_time
                if disconnect_time == self.stop_time:
                    snapshot_time = self.stop_time
                logging.debug(
                    "new snapshot window - connect time: {} - disconnect time: {}".format(
                        connect_time, disconnect_time
                    )
                )

    def _query_exchange_markets(self):
        query = f"""
            select e.name, buy_sym_id, sell_sym_id, e.id
            from {models.Event.__tablename__} ev
            inner join {models.Exchange.__tablename__} e on ev.exchange_id = e.id
            where data_collected = 'agg_order_book'
            group by e.name, buy_sym_id, sell_sym_id, e.id
            """
        return self.session.execute(query)

    def _query_latest_snapshot(self, exchange):
        query = f"""
            select max(timestamp), buy_sym_id, sell_sym_id, exchange_id, e.name, mid_price_range, snapshot_type
            from {models.OrderBookSnapshot.__tablename__} obs
            inner join {models.Exchange.__tablename__} e on obs.exchange_id = e.id
            where e.name = :exchange
            group by buy_sym_id, sell_sym_id, exchange_id, e.name, mid_price_range, snapshot_type;
            """
        return self.session.execute(query, {"exchange": exchange.lower()})

    def _query_connection_events(self):
        query = f"""
            select ev.id, e.name, timestamp, connection_event, data_collected, buy_sym_id, sell_sym_id
            from {models.Event.__tablename__} ev
            inner join {models.Exchange.__tablename__} e on ev.exchange_id = e.id
            where (data_collected = 'agg_order_book'
            or (connection_event = 'disconnect' and data_collected = 'all'))
            order by buy_sym_id, sell_sym_id, timestamp asc
            """
        return self.session.execute(query)

    def _get_last_update_time(self, key, updates):
        snapshot_type = "mid_price_range" if self.mid_price_range else "quartile"
        key = key + str(self.mid_price_range) + snapshot_type
        if key in updates.keys():
            return updates[key]
        else:
            return None

    def _parse_snapshot_times(self, snapshot_updates):
        update_times = {}
        for update in list(snapshot_updates):
            update_times[
                str(update[4])
                + str(update[1])
                + str(update[2])
                + str(update[5])
                + str(update[6])
            ] = update[0]
        return update_times

    def _parse_connection_events(self, events):
        self.event_log = defaultdict(list)
        for event in list(events):
            self.event_log[str(event[1]) + str(event[5]) + str(event[6])].append(
                dict(timestamp=event[2], id=event[0], connection_event=event[3])
            )

    def _parse_exchange_markets(self, exchange_markets):
        exchange_markets = list(exchange_markets)
        if len(exchange_markets) == 0:
            return None
        all_markets = defaultdict(list)
        for market in exchange_markets:
            all_markets[market[0]].append(
                dict(
                    buy_sym_id=market[1],
                    sell_sym_id=market[2],
                    exchange=market[0],
                    exchange_id=market[3],
                )
            )
        return all_markets

    def _query_order_book_quartile(
        self, exchange, buy_sym_id, sell_sym_id, start_time, stop_time
    ):
        logging.debug("QUERY - quartile - order book")
        query = f"""
            with order_book as (
            with latest_orders as (
            select order_type, price, max(last_update_id) max_update_id, exchange_id
            from {models.AggOrder.__tablename__} ag
            where timestamp <= :stop_time
            and timestamp >= :start_time
            group by ag.price, ag.order_type, ag.exchange_id)
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
            where (order_type, price, last_update_id, exchange_id) in (select * from latest_orders)
            and size > 0
            and buy_sym_id = :buy_sym_id
            and sell_sym_id = :sell_sym_id
            and name = :exchange
            and timestamp <= :stop_time
            and timestamp >= :start_time
            )
            select *
            from order_book where (order_book.order_type = 'bid' and order_book.price >= (
                select percentile_disc(0.75) within group (order by order_book.price)
                from order_book
                    where order_book.order_type = 'bid'
            )) or (order_book.order_type = 'ask' and order_book.price <= (
                select percentile_disc(0.25) within group (order by order_book.price)
                from order_book
                    where order_book.order_type = 'ask'
            ))
            """
        return self.session.execute(
            query,
            {
                "stop_time": stop_time,
                "start_time": start_time,
                "buy_sym_id": buy_sym_id.upper(),
                "sell_sym_id": sell_sym_id.upper(),
                "exchange": exchange.lower(),
            },
        )

    def _query_order_book_mid_price(
        self, exchange, buy_sym_id, sell_sym_id, start_time, stop_time
    ):
        logging.debug("QUERY - mid price - order book")
        query = """
        with order_book as (
            with latest_orders as (
                select order_type, price, max(last_update_id) max_update_id, exchange_id
                from aggregate_orders
                where timestamp >= :start_time
                and timestamp <= :stop_time
                group by aggregate_orders.price, aggregate_orders.order_type, aggregate_orders.exchange_id)
            select order_type,
                price,
                size,
                last_update_id,
                timestamp,
                name,
                buy_sym_id,
                sell_sym_id
            from aggregate_orders
                    inner join exchanges on aggregate_orders.exchange_id = exchanges.id
            where (order_type, price, last_update_id, exchange_id) in (select * from latest_orders)
            and size > 0
            and buy_sym_id = :buy_sym_id
            and sell_sym_id = :sell_sym_id
            and name = :exchange
            and timestamp >= :start_time
            and timestamp <= :stop_time
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
        where (order_book.order_type = 'bid' and order_book.price >= (1- :range)* mid_price.mid)
        or (order_book.order_type = 'ask' and order_book.price <= (1+ :range)* mid_price.mid)
        order by timestamp desc
        """
        return self.session.execute(
            query,
            {
                "range": self.mid_price_range,
                "stop_time": stop_time,
                "start_time": start_time,
                "buy_sym_id": buy_sym_id.upper(),
                "sell_sym_id": sell_sym_id.upper(),
                "exchange": exchange.lower(),
            },
        )

    def _parse_order_book(self, order_book):
        full_order_book = []
        order_book = list(order_book)
        logging.debug("ORDER BOOK: {}".format(order_book))
        if len(order_book) == 0:
            logging.debug("empty order book to be parsed")
            return None
        for order in order_book:
            full_order_book.append(
                dict(order_type=order[0], price=order[1], size=order[2])
            )
        logging.debug(
            "ob_snapshot_generator - parsed order books: 'full order book' ({} orders)".format(
                len(full_order_book)
            )
        )
        return full_order_book

    def _generate_snapshot(self, full_ob, metadata):
        full_ob_stats = self._compute_stats(full_ob)
        # quartile_ob_stats = self._compute_stats(quartile_ob)
        snapshot_type = "mid_price_range" if self.mid_price_range else "quartile"
        return models.OrderBookSnapshot(
            mid_price_range=self.mid_price_range,
            snapshot_type=snapshot_type,
            exchange_id=metadata["exchange_id"],
            sell_sym_id=metadata["sell_sym_id"],
            buy_sym_id=metadata["buy_sym_id"],
            timestamp=metadata["timestamp"],
            spread=full_ob_stats["spread"],
            bids_volume=full_ob_stats["bids_volume"],
            asks_volume=full_ob_stats["asks_volume"],
            bids_count=full_ob_stats["bids_count"],
            asks_count=full_ob_stats["asks_count"],
            bids_price_stddev=full_ob_stats["bids_price_stddev"],
            asks_price_stddev=full_ob_stats["asks_price_stddev"],
            bids_price_mean=full_ob_stats["bids_price_mean"],
            asks_price_mean=full_ob_stats["asks_price_mean"],
            min_ask_price=full_ob_stats["min_ask_price"],
            min_ask_size=full_ob_stats["min_ask_size"],
            max_bid_price=full_ob_stats["max_bid_price"],
            max_bid_size=full_ob_stats["max_bid_size"],
            bid_price_median=full_ob_stats["bid_price_median"],
            ask_price_median=full_ob_stats["ask_price_median"],
            # bid_price_upper_quartile=quartile_ob_stats["bid_price_upper_quartile"],
            # ask_price_lower_quartile=quartile_ob_stats["ask_price_lower_quartile"],
            # bids_volume_upper_quartile=quartile_ob_stats["bids_volume"],
            # asks_volume_lower_quartile=quartile_ob_stats["asks_volume"],
            # bids_count_upper_quartile=quartile_ob_stats["bids_count"],
            # asks_count_lower_quartile=quartile_ob_stats["asks_count"],
            # bids_price_stddev_upper_quartile=quartile_ob_stats["bids_price_stddev"],
            # asks_price_stddev_lower_quartile=quartile_ob_stats["asks_price_stddev"],
            # bids_price_mean_upper_quartile=quartile_ob_stats["bids_price_mean"],
            # asks_price_mean_lower_quartile=quartile_ob_stats["asks_price_mean"]
        )

    def _compute_stats(self, order_book):
        bids = list(filter(lambda x: x["order_type"] == "bid", order_book))
        asks = list(filter(lambda x: x["order_type"] == "ask", order_book))
        bid_prices = list(map(lambda x: x["price"], bids))
        ask_prices = list(map(lambda x: x["price"], asks))
        avg_bid_price = 0
        if len(bids):
            avg_bid_price = float(sum(d["price"] for d in bids)) / len(bids)
        avg_ask_price = 0
        if len(asks):
            avg_ask_price = float(sum(d["price"] for d in asks)) / len(asks)
        bids_volume = float(sum(d["price"] * d["size"] for d in bids))
        asks_volume = float(sum(d["price"] * d["size"] for d in asks))
        min_ask_size = max(
            list(d["size"] if d["price"] == min(ask_prices) else 0 for d in asks)
        )
        max_bid_size = max(
            list(d["size"] if d["price"] == max(bid_prices) else 0 for d in bids)
        )
        spread = float(float(min(ask_prices)) - float(max(bid_prices)))
        return dict(
            spread=spread,
            min_ask_price=min(ask_prices),
            min_ask_size=min_ask_size,
            max_bid_price=max(bid_prices),
            max_bid_size=max_bid_size,
            bids_volume=bids_volume,
            asks_volume=asks_volume,
            bids_count=len(bids),
            asks_count=len(asks),
            bids_price_stddev=np.std(bid_prices),
            asks_price_stddev=np.std(ask_prices),
            bids_price_mean=avg_bid_price,
            asks_price_mean=avg_ask_price,
            bid_price_median=np.median(bid_prices),
            ask_price_median=np.median(ask_prices),
        )
