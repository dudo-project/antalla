from datetime import datetime
from dateutil.parser import parse as parse_date
from decimal import Decimal
from os import path
import json
import unittest
from unittest.mock import MagicMock


from antalla import models
from antalla import actions
from antalla.exchange_listeners.hitbtc_listener import HitBTCListener

FIXTURES_PATH = path.join(path.dirname(path.dirname(__file__)), "fixtures")

class HitBTCListenerTest(unittest.TestCase):
    def setUp(self):
            self.dummy_exchange = models.Exchange(id=1338, name="dummy")
            self.on_event_mock = MagicMock()
            self.hitbtc_listener = HitBTCListener(self.dummy_exchange, self.on_event_mock)
            self.hitbtc_listener._all_symbols = [
                dict(id="ETHBTC", baseCurrency="ETH", quoteCurrency="BTC"),
                dict(id="LTCBTC", baseCurrency="LTC", quoteCurrency="BTC"),
                ]

    def assertAreAllActions(self, items):
        for item in items:
            self.assertIsInstance(item, actions.Action)

    def raw_fixture(self, fixture_name):
        with open(path.join(FIXTURES_PATH, fixture_name)) as f:
            return f.read()

    def test_parse_markets(self):
        payload = self.raw_fixture("hitbtc/hitbtc-markets.json")
        
        self.hitbtc_listener._all_symbols = [
            dict(id="BCNBTC", baseCurrency="BCN", quoteCurrency="BTC"),
            dict(id="BTCUSD", baseCurrency="BTC", quoteCurrency="USD"),
            dict(id="DASHBTC", baseCurrency="DASH", quoteCurrency="BTC"),
            dict(id="DOGEBTC", baseCurrency="DOGE", quoteCurrency="BTC")
        ]

        parsed_actions = self.hitbtc_listener._parse_markets(json.loads(payload))
        self.assertAreAllActions(parsed_actions)
        self.assertEqual(len(parsed_actions), 3)
        insert_coins = parsed_actions[0]
        insert_markets = parsed_actions[1]
        insert_exchange_markets = parsed_actions[2]
        
        self.assertIsInstance(insert_coins, actions.InsertAction)
        self.assertIsInstance(insert_coins.items[0], models.Coin)

        self.assertEqual(len(insert_markets.items), 4)
        self.assertEqual(len(insert_exchange_markets.items), 4)
        self.assertIsInstance(insert_markets, actions.InsertAction)
        self.assertIsInstance(insert_exchange_markets, actions.InsertAction)
        
        self.assertEqual(insert_markets.items[0].first_coin_id, "BCN")
        self.assertEqual(insert_markets.items[0].second_coin_id, "BTC")
        self.assertEqual(insert_exchange_markets.items[0].exchange_id, self.dummy_exchange.id)
        self.assertEqual(insert_exchange_markets.items[0].quoted_volume_id, "BCN")
        self.assertEqual(insert_exchange_markets.items[0].quoted_volume, 161710600.0)
        self.assertEqual(insert_exchange_markets.items[0].quoted_vol_timestamp, parse_date("2019-04-24T15:10:05.535Z"))

        self.assertEqual(insert_markets.items[1].first_coin_id, "BTC")
        self.assertEqual(insert_markets.items[1].second_coin_id, "USD")
        self.assertEqual(insert_exchange_markets.items[1].exchange_id, self.dummy_exchange.id)
        self.assertEqual(insert_exchange_markets.items[1].quoted_volume_id, "BTC")
        self.assertEqual(insert_exchange_markets.items[1].quoted_volume, 26167.55323)
        self.assertEqual(insert_exchange_markets.items[1].quoted_vol_timestamp, parse_date("2019-04-24T15:10:09.948Z"))
        
        self.assertEqual(insert_markets.items[2].first_coin_id, "BTC")
        self.assertEqual(insert_markets.items[2].second_coin_id, "DASH")
        self.assertEqual(insert_exchange_markets.items[2].exchange_id, self.dummy_exchange.id)
        self.assertEqual(insert_exchange_markets.items[2].quoted_volume_id, "DASH")
        self.assertEqual(insert_exchange_markets.items[2].quoted_volume, 40491.632)
        self.assertEqual(insert_exchange_markets.items[2].quoted_vol_timestamp, parse_date("2019-04-24T15:10:09.836Z"))

        self.assertEqual(insert_markets.items[3].first_coin_id, "BTC")
        self.assertEqual(insert_markets.items[3].second_coin_id, "DOGE")
        self.assertEqual(insert_exchange_markets.items[3].exchange_id, self.dummy_exchange.id)
        self.assertEqual(insert_exchange_markets.items[3].quoted_volume_id, "DOGE")
        self.assertEqual(insert_exchange_markets.items[3].quoted_volume, 719344170.0)
        self.assertEqual(insert_exchange_markets.items[3].quoted_vol_timestamp, parse_date("2019-04-24T15:10:08.539Z"))

    def test_parse_snapshotOrderbook(self):
        self.hitbtc_listener._all_symbols = [
            dict(id="ETHBTC", baseCurrency="ETH", quoteCurrency="BTC"),
        ]
        payload = self.raw_fixture("hitbtc/hitbtc-snapshot.json")
        payload = json.loads(payload)
        payload = payload["params"]
        parsed_actions = self.hitbtc_listener._parse_snapshotOrderbook(payload)
        self.assertAreAllActions(parsed_actions)
        self.assertEqual(len(parsed_actions), 1)
        insert_action = parsed_actions[0]
        self.assertIsInstance(insert_action, actions.InsertAction)
        self.assertEqual(len(insert_action.items), 6)
        self.assertIsInstance(insert_action.items[0], models.AggOrder)
        self.assertEqual(insert_action.items[0].exchange_id, self.dummy_exchange.id)
        self.assertEqual(insert_action.items[0].buy_sym_id, "ETH")
        self.assertEqual(insert_action.items[0].sell_sym_id, "BTC")
        self.assertEqual(insert_action.items[0].order_type, "bid")
        self.assertEqual(insert_action.items[0].price, 0.054558)
        self.assertEqual(insert_action.items[0].size, 0.500)
        self.assertEqual(insert_action.items[0].timestamp, parse_date("2018-11-19T05:00:28.193Z"))

        self.assertEqual(insert_action.items[3].exchange_id, self.dummy_exchange.id)
        self.assertEqual(insert_action.items[3].buy_sym_id, "ETH")
        self.assertEqual(insert_action.items[3].sell_sym_id, "BTC")
        self.assertEqual(insert_action.items[3].order_type, "ask")
        self.assertEqual(insert_action.items[3].price, 0.054588)
        self.assertEqual(insert_action.items[3].size, 0.245)
        self.assertEqual(insert_action.items[3].timestamp, parse_date("2018-11-19T05:00:28.193Z"))
        
    def test_parse_raw_trades(self):
        payload = self.raw_fixture("hitbtc/hitbtc-update-trades.json")
        payload = json.loads(payload)
        payload = payload["params"]
        parsed_actions = self.hitbtc_listener._parse_raw_trades(payload)
        self.assertAreAllActions(parsed_actions)
        self.assertEqual(len(parsed_actions), 1)
        insert_action = parsed_actions[0]
        self.assertIsInstance(insert_action, actions.InsertAction)
        self.assertEqual(len(insert_action.items), 1)
        self.assertIsInstance(insert_action.items[0], models.Trade)
        self.assertEqual(insert_action.items[0].exchange_id, self.dummy_exchange.id)
        self.assertEqual(insert_action.items[0].buy_sym_id, "ETH")
        self.assertEqual(insert_action.items[0].sell_sym_id, "BTC")
        self.assertEqual(insert_action.items[0].size, 0.183)
        self.assertEqual(insert_action.items[0].price, 0.054670)
        self.assertEqual(insert_action.items[0].trade_type, "buy")
        self.assertEqual(insert_action.items[0].id, 54469813)
        self.assertEqual(insert_action.items[0].timestamp, parse_date("2017-10-19T16:34:25.041Z"))

    def test_parse_update_orderbook(self):
        payload = self.raw_fixture("hitbtc/hitbtc-update-orderbook.json")
        payload = json.loads(payload)
        payload = payload["params"]
        parsed_actions = self.hitbtc_listener._parse_updateOrderbook(payload)
        self.assertAreAllActions(parsed_actions)
        self.assertEqual(len(parsed_actions), 1)
        insert_action = parsed_actions[0]
        self.assertIsInstance(insert_action, actions.InsertAction)
        self.assertEqual(len(insert_action.items), 3)
        self.assertIsInstance(insert_action.items[0], models.AggOrder)
        self.assertEqual(insert_action.items[0].exchange_id, self.dummy_exchange.id)
        self.assertEqual(insert_action.items[0].buy_sym_id, "ETH")
        self.assertEqual(insert_action.items[0].sell_sym_id, "BTC")
        self.assertEqual(insert_action.items[0].order_type, "bid")
        self.assertEqual(insert_action.items[0].price, 0.054504)
        self.assertEqual(insert_action.items[0].size, 0)
        self.assertEqual(insert_action.items[0].sequence_id, "8073830")
        self.assertEqual(insert_action.items[0].timestamp, parse_date("2018-11-19T05:00:28.700Z"))

        self.assertEqual(insert_action.items[2].exchange_id, self.dummy_exchange.id)
        self.assertEqual(insert_action.items[2].buy_sym_id, "ETH")
        self.assertEqual(insert_action.items[2].sell_sym_id, "BTC")
        self.assertEqual(insert_action.items[2].order_type, "ask")
        self.assertEqual(insert_action.items[2].price, 0.054591)
        self.assertEqual(insert_action.items[2].size, 0)
        self.assertEqual(insert_action.items[2].sequence_id, "8073828")
        self.assertEqual(insert_action.items[2].timestamp, parse_date("2018-11-19T05:00:28.700Z"))
