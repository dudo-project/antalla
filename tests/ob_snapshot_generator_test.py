import unittest
from datetime import datetime

from antalla import db
from antalla import models
from antalla import ob_snapshot_generator
from tests.fixtures import dummy_db


class ModelsTest(unittest.TestCase):
    def setUp(self):
        self.session = db.Session()
        self.session.commit = lambda: None

    def tearDown(self):
        self.session.rollback()

    def _insert_data(self):
        dummy_db.insert_agg_order(self.session)
        dummy_db.insert_coins(self.session)
        dummy_db.insert_events(self.session)
        dummy_db.insert_exchange_markets(self.session)
        dummy_db.insert_exchanges(self.session)
        dummy_db.insert_markets(self.session)
        self.session.flush()

    def test_query_exchange_markets(self):
        self._insert_data()
        generator = ob_snapshot_generator.OBSnapshotGenerator(
            "hitbtc", datetime.now(), session=self.session
        )
        exchange_markets = generator._query_exchange_markets()
        parsed_exchange_markets = generator._parse_exchange_markets(exchange_markets)
        self.assertEqual(
            parsed_exchange_markets["hitbtc"],
            [
                dict(
                    buy_sym_id="ETH",
                    sell_sym_id="BTC",
                    exchange="hitbtc",
                    exchange_id=1,
                )
            ],
        )

    def test_query_connection_events(self):
        self._insert_data()
        generator = ob_snapshot_generator.OBSnapshotGenerator(
            "hitbtc", datetime.now(), session=self.session
        )
        connection_events = generator._query_connection_events()
        generator._parse_connection_events(connection_events)
        for ex in generator.event_log.keys():
            for ev in generator.event_log[ex]:
                del ev["id"]
        self.assertEqual(
            generator.event_log["hitbtcETHBTC"][0],
            dict(
                timestamp=datetime(2019, 5, 15, 19, 30, 0, 0),
                connection_event="connect",
            ),
        )
        self.assertEqual(
            generator.event_log["hitbtcETHBTC"][1],
            dict(
                timestamp=datetime(2019, 5, 15, 19, 35, 45, 0),
                connection_event="disconnect",
            ),
        )
        self.assertEqual(
            generator.event_log["hitbtcETHBTC"][2],
            dict(
                timestamp=datetime(2019, 5, 15, 19, 36, 0, 0),
                connection_event="connect",
            ),
        )
        self.assertEqual(
            generator.event_log["hitbtcETHBTC"][3],
            dict(
                timestamp=datetime(2019, 5, 15, 19, 38, 0, 0),
                connection_event="disconnect",
            ),
        )
        self.assertEqual(
            generator.event_log["hitbtcETHBTC"][4],
            dict(
                timestamp=datetime(2019, 5, 15, 19, 39, 0, 0),
                connection_event="connect",
            ),
        )
        self.assertEqual(
            generator.event_log["binanceETHBTC"][0],
            dict(
                timestamp=datetime(2019, 5, 15, 19, 34, 30, 0),
                connection_event="connect",
            ),
        )
        self.assertEqual(
            generator.event_log["binanceETHBTC"][1],
            dict(
                timestamp=datetime(2019, 5, 15, 19, 38, 34, 0),
                connection_event="disconnect",
            ),
        )

    def test_generate_snapshot_1(self):
        self._insert_data()
        generator = ob_snapshot_generator.OBSnapshotGenerator(
            "hitbtc", datetime(2019, 5, 15, 19, 35, 42, 0), session=self.session
        )
        connection_events = generator._query_connection_events()
        generator._parse_connection_events(connection_events)
        generator.snapshot_interval = 1
        market = dict(exchange_id=1, buy_sym_id="ETH", sell_sym_id="BTC")
        exchange = "hitbtc"
        connect_time = datetime(2019, 5, 15, 19, 30, 0, 0)
        disconnect_time = datetime(2019, 5, 15, 19, 35, 45, 0)
        snapshot_time = datetime(2019, 5, 15, 19, 34, 59, 0)
        generator._generate_all_snapshots(
            connect_time, disconnect_time, snapshot_time, market, exchange
        )
        created_snapshots = list(
            self.session.execute(
                f"""select count(*) from {models.OrderBookSnapshot.__tablename__}
                where timestamp >= '2019-05-15 19:34:59.0' and timestamp <= '2019-05-15 19:35:45.0'"""
            )
        )[0]
        self.assertEqual(created_snapshots[0], 42)

    def test_generate_snapshot_2(self):
        self._insert_data()
        generator = ob_snapshot_generator.OBSnapshotGenerator(
            "hitbtc", datetime(2019, 5, 15, 19, 35, 11, 0), session=self.session
        )
        connection_events = generator._query_connection_events()
        generator._parse_connection_events(connection_events)
        generator.snapshot_interval = 1
        market = dict(exchange_id=1, buy_sym_id="ETH", sell_sym_id="BTC")
        exchange = "hitbtc"
        snapshot_time = datetime(2019, 5, 15, 19, 34, 0, 0)
        connect_time, disconnect_time = generator._get_connection_window(
            snapshot_time, "hitbtcETHBTC"
        )
        generator._generate_all_snapshots(
            connect_time, disconnect_time, snapshot_time, market, exchange
        )
        created_snapshots = list(
            self.session.execute(
                f"select count(*) from {models.OrderBookSnapshot.__tablename__}"
            )
        )[0]
        self.assertEqual(created_snapshots[0], 70)

    def test_generate_snapshot_3(self):
        """counts the number of snapshots submitted over two different connection windows with a mid starting point
        in the first window
        """
        dummy_db.insert_agg_order(self.session)
        dummy_db.insert_coins(self.session)
        dummy_db.insert_instable_connection_events(self.session)
        dummy_db.insert_exchange_markets(self.session)
        dummy_db.insert_exchanges(self.session)
        dummy_db.insert_markets(self.session)
        self.session.flush()
        generator = ob_snapshot_generator.OBSnapshotGenerator(
            "hitbtc", datetime(2019, 5, 15, 19, 32, 41, 0), session=self.session
        )
        connection_events = generator._query_connection_events()
        generator._parse_connection_events(connection_events)
        generator.snapshot_interval = 1
        market = dict(exchange_id=1, buy_sym_id="ETH", sell_sym_id="BTC")
        exchange = "hitbtc"
        snapshot_time = datetime(2019, 5, 15, 19, 30, 45, 0)
        connect_time, disconnect_time = generator._get_connection_window(
            snapshot_time, "hitbtcETHBTC"
        )
        generator._generate_all_snapshots(
            connect_time, disconnect_time, snapshot_time, market, exchange
        )
        created_snapshots = list(
            self.session.execute(
                f"select count(*) from {models.OrderBookSnapshot.__tablename__}"
            )
        )[0]
        self.assertEqual(created_snapshots[0], 109)

    def test_query_order_book(self):
        self._insert_data()
        generator = ob_snapshot_generator.OBSnapshotGenerator(
            "hitbtc", datetime.now(), 1, session=self.session
        )
        ob_result_proxy = generator._query_order_book(
            "hitbtc", "ETH", "BTC", "2019-05-15 19:30:0.0", "2019-05-15 19:35:45.0"
        )
        full_order_book = generator._parse_order_book(ob_result_proxy)
        self.assertEqual(len(full_order_book), 6)
        bids = 0
        asks = 0
        bids = list(filter(lambda x: x["order_type"] == "bid", full_order_book))
        asks = list(filter(lambda x: x["order_type"] == "ask", full_order_book))
        bid_prices = list(map(lambda x: x["price"], bids))
        ask_prices = list(map(lambda x: x["price"], asks))
        self.assertEqual(len(bids), 3)
        self.assertEqual(len(asks), 3)
        self.assertAlmostEqual(min(bid_prices), 0.3)
        self.assertAlmostEqual(min(ask_prices), 0.6)
        self.assertAlmostEqual(max(bid_prices), 0.5)
        self.assertAlmostEqual(max(ask_prices), 0.7)

    def test_get_connection_window(self):
        self._insert_data()
        generator = ob_snapshot_generator.OBSnapshotGenerator(
            "hitbtc", datetime.now(), session=self.session
        )
        connection_events = generator._query_connection_events()
        generator._parse_connection_events(connection_events)
        connect_time, disconnect_time = generator._get_connection_window(
            datetime(2019, 5, 15, 19, 35, 30, 0), "hitbtcETHBTC"
        )
        self.assertEqual(connect_time, datetime(2019, 5, 15, 19, 30, 0, 0))
        self.assertEqual(disconnect_time, datetime(2019, 5, 15, 19, 35, 45, 0))
        connect_time, disconnect_time = generator._get_connection_window(
            datetime(2019, 5, 15, 19, 37, 30, 0), "hitbtcETHBTC"
        )
        self.assertEqual(connect_time, datetime(2019, 5, 15, 19, 36, 0, 0))
        self.assertEqual(disconnect_time, datetime(2019, 5, 15, 19, 38, 0, 0))
        connect_time, disconnect_time = generator._get_connection_window(
            datetime(2019, 5, 15, 19, 39, 0, 0), "hitbtcETHBTC"
        )
        self.assertEqual(connect_time, datetime(2019, 5, 15, 19, 39, 0, 0))
        self.assertEqual(disconnect_time, generator.stop_time)
        connect_time, disconnect_time = generator._get_connection_window(
            datetime(2019, 5, 15, 19, 45, 30, 0), "hitbtcETHBTC"
        )
        self.assertEqual(connect_time, datetime(2019, 5, 15, 19, 39, 0, 0))
        self.assertEqual(disconnect_time, generator.stop_time)
        connect_time, disconnect_time = generator._get_connection_window(
            datetime(2019, 5, 15, 19, 34, 44, 0), "binanceETHBTC"
        )
        self.assertEqual(connect_time, datetime(2019, 5, 15, 19, 34, 30, 0))
        self.assertEqual(disconnect_time, datetime(2019, 5, 15, 19, 38, 34, 0))
        connect_time, disconnect_time = generator._get_connection_window(
            datetime(2019, 5, 15, 19, 34, 0, 0), "hitbtcETHBTC"
        )
        self.assertEqual(connect_time, datetime(2019, 5, 15, 19, 30, 0, 0))
        self.assertEqual(disconnect_time, datetime(2019, 5, 15, 19, 35, 45, 0))
        connect_time, disconnect_time = generator._get_connection_window(
            datetime(2019, 5, 15, 19, 35, 45, 0), "hitbtcETHBTC"
        )
        self.assertEqual(connect_time, datetime(2019, 5, 15, 19, 36, 0, 0))
        self.assertEqual(disconnect_time, datetime(2019, 5, 15, 19, 38, 0, 0))

    def test_compute_stats(self):
        order_book = [
            {"order_type": "bid", "price": 0.5, "size": 10},
            {"order_type": "ask", "price": 1.1, "size": 5},
            {"order_type": "bid", "price": 0.75, "size": 30},
            {"order_type": "bid", "price": 0.8, "size": 5},
            {"order_type": "ask", "price": 1.08, "size": 4},
            {"order_type": "ask", "price": 1.02, "size": 7},
            {"order_type": "bid", "price": 0.95, "size": 7},
            {"order_type": "ask", "price": 0.97, "size": 3},
        ]
        generator = ob_snapshot_generator.OBSnapshotGenerator("hitbtc", 0)
        output = generator._compute_stats(order_book)
        self.assertEqual(output["spread"], 0.020000000000000018)
        self.assertEqual(output["min_ask_price"], 0.97)
        self.assertEqual(output["min_ask_size"], 3)
        self.assertEqual(output["max_bid_price"], 0.95)
        self.assertEqual(output["max_bid_size"], 7)
        self.assertEqual(output["bids_volume"], 38.15)
        self.assertEqual(output["asks_volume"], 19.87)
        self.assertEqual(output["bids_count"], 4)
        self.assertEqual(output["asks_count"], 4)
        self.assertEqual(output["bids_price_stddev"], 0.1620185174601965)
        self.assertEqual(output["asks_price_stddev"], 0.05117372372614685)
        self.assertEqual(output["bids_price_mean"], 0.75)
        self.assertEqual(output["asks_price_mean"], 1.0425)
        self.assertEqual(output["bid_price_median"], 0.775)
        self.assertEqual(output["ask_price_median"], 1.05)

    def test_run_mid_price(self):
        """testing the computation of order book snapshots using a mid price range approach"""
        dummy_db.insert_agg_orders_snapshot(self.session)
        dummy_db.insert_coins(self.session)
        dummy_db.insert_events_snapshot(self.session)
        dummy_db.insert_exchange_markets(self.session)
        dummy_db.insert_exchanges(self.session)
        dummy_db.insert_markets(self.session)
        self.session.flush()
        interval = 60
        mid_price_range = 0.1

        # Check 1
        generator = ob_snapshot_generator.OBSnapshotGenerator(
            "hitbtc",
            datetime(2019, 5, 1, 1, 2, 0, 0),
            mid_price_range,
            interval,
            session=self.session,
        )
        generator.run()
        all_snapshots = self.session.execute(
            f"""select timestamp, spread, bids_count, asks_count, bids_volume, asks_volume,
                       bids_price_stddev, asks_price_stddev, bids_price_mean, asks_price_mean
                from {models.OrderBookSnapshot.__tablename__} snap
                inner join {models.Exchange.__tablename__} ex on snap.exchange_id = ex.id
                where ex.name = 'hitbtc' order by timestamp asc"""
        )
        results = list(all_snapshots)
        self.assertEqual(len(results), 1)
        self.assertAlmostEqual(results[0][1], 0.1)
        self.assertEqual(results[0][2], 1)
        self.assertEqual(results[0][3], 1)
        self.assertEqual(results[0][4], 45.0)
        self.assertEqual(results[0][5], 92.0)

        # Check 2
        generator = ob_snapshot_generator.OBSnapshotGenerator(
            "hitbtc",
            datetime(2019, 5, 1, 1, 6, 0, 0),
            mid_price_range,
            interval,
            session=self.session,
        )
        generator.run()
        all_snapshots = self.session.execute(
            f"""select timestamp, spread, bids_count, asks_count, bids_volume, asks_volume, bids_price_stddev,
                        asks_price_stddev, bids_price_mean, asks_price_mean
                from {models.OrderBookSnapshot.__tablename__} snap
                inner join {models.Exchange.__tablename__} ex on snap.exchange_id = ex.id
                where ex.name = 'hitbtc' order by timestamp asc"""
        )
        results = list(all_snapshots)
        # five snapshots have been generated - last bid added is not included due to being out of range
        self.assertEqual(len(results), 5)
        self.assertAlmostEqual(results[4][1], 0.1)
        self.assertEqual(results[4][2], 4)
        self.assertEqual(results[4][3], 4)
        self.assertAlmostEqual(results[4][4], 174.2)
        self.assertAlmostEqual(results[4][5], 248.7)
        self.assertAlmostEqual(results[4][6], 0.11180339887498948)
        self.assertAlmostEqual(results[4][7], 0.11180339887498948)

        # Check 3
        generator = ob_snapshot_generator.OBSnapshotGenerator(
            "hitbtc",
            datetime(2019, 5, 1, 1, 9, 0, 0),
            mid_price_range,
            interval,
            session=self.session,
        )
        generator.run()
        all_snapshots = self.session.execute(
            f"""select timestamp, spread, bids_count, asks_count, bids_volume, asks_volume, bids_price_stddev,
                       asks_price_stddev, bids_price_mean, asks_price_mean
                from {models.OrderBookSnapshot.__tablename__} snap
                inner join {models.Exchange.__tablename__} ex
                on snap.exchange_id = ex.id where ex.name = 'hitbtc' order by timestamp asc"""
        )
        results = list(all_snapshots)
        # eight snapshots have been generated - last five orders are ignored due to being out of range
        self.assertEqual(len(results), 8)
        self.assertAlmostEqual(results[7][1], 0.1)
        self.assertEqual(results[7][2], 4)
        self.assertEqual(results[7][3], 4)
        self.assertAlmostEqual(results[7][4], 174.2)
        self.assertAlmostEqual(results[7][5], 248.7)
        self.assertAlmostEqual(results[7][6], 0.11180339887498948)
        self.assertAlmostEqual(results[7][7], 0.11180339887498948)

        # Check 4
        generator = ob_snapshot_generator.OBSnapshotGenerator(
            "hitbtc",
            datetime(2019, 5, 1, 1, 10, 0, 0),
            mid_price_range,
            interval,
            session=self.session,
        )
        generator.run()
        all_snapshots = self.session.execute(
            f"""select timestamp, spread, bids_count, asks_count, bids_volume, asks_volume, bids_price_stddev,\
                       asks_price_stddev, bids_price_mean, asks_price_mean
                from {models.OrderBookSnapshot.__tablename__} snap
                inner join {models.Exchange.__tablename__} ex
                on snap.exchange_id = ex.id where ex.name = 'hitbtc'
                order by timestamp asc"""
        )
        results = list(all_snapshots)
        # nine snapshots have been generated - last order sets a new mid price
        self.assertEqual(len(results), 9)
        self.assertAlmostEqual(results[8][1], 0.2)
        self.assertEqual(results[8][2], 3)
        self.assertEqual(results[8][3], 4)
        self.assertAlmostEqual(results[8][4], 129.2)
        self.assertAlmostEqual(results[8][5], 248.7)
        self.assertAlmostEqual(results[8][6], 0.08164965809277268)
        self.assertAlmostEqual(results[8][7], 0.11180339887498948)

        # Check 5
        generator = ob_snapshot_generator.OBSnapshotGenerator(
            "hitbtc",
            datetime(2019, 5, 1, 1, 11, 0, 0),
            mid_price_range,
            interval,
            session=self.session,
        )
        generator.run()
        all_snapshots = self.session.execute(
            f"""select timestamp, spread, bids_count, asks_count, bids_volume, asks_volume, bids_price_stddev,
                        asks_price_stddev, bids_price_mean, asks_price_mean
                from {models.OrderBookSnapshot.__tablename__} snap
                inner join {models.Exchange.__tablename__} ex on snap.exchange_id = ex.id
                where ex.name = 'hitbtc'
                order by timestamp asc"""
        )
        results = list(all_snapshots)
        # ten snapshots have been generated - last order is a new ask order which should be included in snapshot
        self.assertEqual(len(results), 10)
        self.assertAlmostEqual(results[9][1], 0.2)
        self.assertEqual(results[9][2], 3)
        self.assertEqual(results[9][3], 5)
        self.assertAlmostEqual(results[9][4], 129.2)
        self.assertAlmostEqual(results[9][5], 297.2)
        self.assertAlmostEqual(results[9][6], 0.08164965809277268)
        self.assertAlmostEqual(results[9][7], 0.10770329614269018)
        self.assertAlmostEqual(results[9][8], 4.3)
        self.assertAlmostEqual(results[9][9], 4.77)

        # Check 6: mid price +- 20%
        mid_price_range = 0.2
        generator = ob_snapshot_generator.OBSnapshotGenerator(
            "hitbtc",
            datetime(2019, 5, 1, 1, 11, 0, 0),
            mid_price_range,
            interval,
            session=self.session,
        )
        generator.run()
        all_snapshots = self.session.execute(
            f"""select timestamp, spread, bids_count, asks_count, bids_volume, asks_volume, bids_price_stddev,
                       asks_price_stddev, bids_price_mean, asks_price_mean
                from {models.OrderBookSnapshot.__tablename__} snap
                inner join {models.Exchange.__tablename__} ex on snap.exchange_id = ex.id where ex.name = 'hitbtc'
                order by timestamp asc"""
        )
        results = list(all_snapshots)
        # ten snapshots have been generated - mid price range is changed to +-20%
        # total of 20 snapshots in db: 10 @ range +-10% and 10 @ range +-20%
        self.assertEqual(len(results), 20)
        self.assertAlmostEqual(results[19][1], 0.2)
        self.assertEqual(results[19][2], 6)
        self.assertEqual(results[19][3], 6)
        self.assertAlmostEqual(results[19][4], 201.8)
        self.assertAlmostEqual(results[19][5], 318.0)
        self.assertAlmostEqual(results[19][6], 0.25603819159562036)
        self.assertAlmostEqual(results[19][7], 0.18800856954464143)
        self.assertAlmostEqual(results[19][8], 4.066666666666666)
        self.assertAlmostEqual(results[19][9], 4.841666666666667)

    def test_run_quartile(self):
        """testing the computation of order book snapshots using a quartile approach"""
        dummy_db.insert_agg_orders_snapshot(self.session)
        dummy_db.insert_coins(self.session)
        dummy_db.insert_events_snapshot(self.session)
        dummy_db.insert_exchange_markets(self.session)
        dummy_db.insert_exchanges(self.session)
        dummy_db.insert_markets(self.session)
        self.session.flush()
        interval = 60
        mid_price_range = 0

        # Check 1
        generator = ob_snapshot_generator.OBSnapshotGenerator(
            "hitbtc",
            datetime(2019, 5, 1, 1, 6, 0, 0),
            mid_price_range,
            interval,
            session=self.session,
        )
        generator.run()
        all_snapshots = self.session.execute(
            f"""select timestamp, spread, bids_count, asks_count, bids_volume, asks_volume, bids_price_stddev, asks_price_stddev, bids_price_mean, asks_price_mean
            from {models.OrderBookSnapshot.__tablename__} snap
            inner join {models.Exchange.__tablename__} ex on snap.exchange_id = ex.id where ex.name = 'hitbtc'
            order by timestamp asc"""
        )
        results = list(all_snapshots)
        self.assertEqual(len(results), 5)
        self.assertAlmostEqual(results[4][1], 0.1)
        self.assertEqual(results[4][2], 2)
        self.assertEqual(results[4][3], 1)
        self.assertAlmostEqual(results[4][4], 97.8)
        self.assertAlmostEqual(results[4][5], 92.0)
        self.assertAlmostEqual(results[4][6], 0.0499, delta=0.001)
        self.assertAlmostEqual(results[4][7], 0.0)
        self.assertAlmostEqual(results[4][8], 4.45)
        self.assertAlmostEqual(results[4][9], 4.6)

        # Check 2
        generator = ob_snapshot_generator.OBSnapshotGenerator(
            "hitbtc",
            datetime(2019, 5, 1, 1, 11, 0, 0),
            mid_price_range,
            interval,
            session=self.session,
        )
        generator.run()
        all_snapshots = self.session.execute(
            f"""select timestamp, spread, bids_count, asks_count, bids_volume, asks_volume, bids_price_stddev, asks_price_stddev, bids_price_mean, asks_price_mean
            from {models.OrderBookSnapshot.__tablename__} snap
            inner join {models.Exchange.__tablename__} ex
            on snap.exchange_id = ex.id where ex.name = 'hitbtc' order by timestamp asc"""
        )
        results = list(all_snapshots)
        self.assertEqual(len(results), 10)
        self.assertAlmostEqual(results[9][1], 0.2)
        self.assertEqual(results[9][2], 2)
        self.assertEqual(results[9][3], 2)
        self.assertAlmostEqual(results[9][4], 87.2)
        self.assertAlmostEqual(results[9][5], 195.4)
        self.assertAlmostEqual(results[9][6], 0.05, delta=0.001)
        self.assertAlmostEqual(results[9][7], 0.05, delta=0.001)
        self.assertAlmostEqual(results[9][8], 4.35)
        self.assertAlmostEqual(results[9][9], 4.65)

    def parse_snapshot(self, snapshot):
        all_snapshots = []
        for s in snapshot:
            all_snapshots.append(
                dict(
                    timestamp=s[0],
                    spread=s[1],
                    bids_count=s[2],
                    asks_count=s[3],
                    bids_vol=s[4],
                    asks_vol=s[5],
                    bids_stddev=s[6],
                    asks_stdev=s[7],
                    bids_price_mean=s[8],
                    asks_price_mean=s[9],
                )
            )
        return all_snapshots
