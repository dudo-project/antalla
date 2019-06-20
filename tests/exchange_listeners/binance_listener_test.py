from datetime import datetime
from dateutil.parser import parse as parse_date
from decimal import Decimal
from os import path
import json
import unittest
from unittest.mock import MagicMock


from antalla import models
from antalla import actions
from antalla.exchange_listeners.binance_listener import BinanceListener

FIXTURES_PATH = path.join(path.dirname(path.dirname(__file__)), "fixtures")


class BinanceListenerTest(unittest.TestCase):
    def setUp(self):
        self.dummy_exchange = models.Exchange(id=1338, name="dummy")
        self.on_event_mock = MagicMock()
        self.binance_listener = BinanceListener(self.dummy_exchange, self.on_event_mock)

    def test_parse_depth_update(self):
        payload = self.raw_fixture("binance/binance-depth-update.json")
        parsed_actions = self.binance_listener._parse_depthUpdate(json.loads(payload))
        self.assertAreAllActions(parsed_actions)
        self.assertEqual(len(parsed_actions), 1)
        insert_action = parsed_actions[0]
        self.assertIsInstance(insert_action, actions.InsertAction)
        self.assertEqual(len(insert_action.items), 3)
        order_0 = insert_action.items[0]
        order_1= insert_action.items[1]
        order_2 = insert_action.items[2]
        self.assertEqual(order_0.exchange, self.dummy_exchange)
        self.assertEqual(order_0.buy_sym_id, "BNB")
        self.assertEqual(order_0.sell_sym_id, "BTC")
        self.assertEqual(order_0.last_update_id, 161)
        self.assertEqual(order_0.price, 0.0024)
        self.assertEqual(order_0.size, 10.0)
        self.assertEqual(order_0.order_type, "bid")
        self.assertEqual(order_0.exchange, self.dummy_exchange)
        self.assertEqual(order_1.buy_sym_id, "BNB")
        self.assertEqual(order_1.sell_sym_id, "BTC")
        self.assertEqual(order_1.last_update_id, 161)
        self.assertEqual(order_1.price, 0.0038)
        self.assertEqual(order_1.size, 8.0)
        self.assertEqual(order_0.order_type, "bid")
        self.assertEqual(order_2.exchange, self.dummy_exchange)
        self.assertEqual(order_2.buy_sym_id, "BNB")
        self.assertEqual(order_2.sell_sym_id, "BTC")
        self.assertEqual(order_2.last_update_id, 161)
        self.assertEqual(order_2.price, 0.0026)
        self.assertEqual(order_2.size, 100.0)
        self.assertEqual(order_2.order_type, "ask")
        
    def test_parse_snapshot(self):
        pair = "BNBBTC"
        payload = self.raw_fixture("binance/binance-snapshot.json")
        parsed_actions = self.binance_listener._parse_snapshot(json.loads(payload), pair)
        self.assertAreAllActions(parsed_actions)
        self.assertEqual(len(parsed_actions), 1)
        insert_action = parsed_actions[0]
        self.assertIsInstance(insert_action, actions.InsertAction)
        self.assertEqual(len(insert_action.items), 5)
        order_0 = insert_action.items[0]
        order_4= insert_action.items[4]
        self.assertEqual(order_0.exchange, self.dummy_exchange)
        self.assertEqual(order_0.buy_sym_id, "BNB")
        self.assertEqual(order_0.sell_sym_id, "BTC")
        self.assertEqual(order_0.last_update_id, 1027024)
        self.assertEqual(order_0.price, 4.00000000)
        self.assertEqual(order_0.size, 431.00000000)
        self.assertEqual(order_0.order_type, "bid")
        self.assertEqual(order_0.exchange, self.dummy_exchange)
        self.assertEqual(order_4.buy_sym_id, "BNB")
        self.assertEqual(order_4.sell_sym_id, "BTC")
        self.assertEqual(order_4.last_update_id, 1027024)
        self.assertEqual(order_4.price, 5.00000000)
        self.assertEqual(order_4.size, 60.00000000)
        self.assertEqual(order_4.order_type, "ask")
        
    def test_parse_trade(self):
        payload = self.raw_fixture("binance/binance-trade.json")
        parsed_actions = self.binance_listener._parse_trade(json.loads(payload))
        self.assertAreAllActions(parsed_actions)
        self.assertEqual(len(parsed_actions), 1)
        insert_action = parsed_actions[0]
        self.assertIsInstance(insert_action, actions.InsertAction)
        self.assertEqual(len(insert_action.items), 1)
        trade = insert_action.items[0]
        self.assertEqual(trade.buy_sym_id, "BNB")
        self.assertEqual(trade.sell_sym_id, "BTC")
        self.assertEqual(trade.size, 100.0)
        self.assertEqual(trade.price, 0.001)

    def test_parse_markets(self):
        payload = self.raw_fixture("binance/binance-markets.json")
        parsed_actions = self.binance_listener._parse_markets(json.loads(payload))
        self.assertAreAllActions(parsed_actions)
        self.assertEqual(len(parsed_actions), 3)
        insert_coins = parsed_actions[0]
        insert_markets = parsed_actions[1]
        insert_exchange_markets = parsed_actions[2]

        self.assertIsInstance(insert_coins, actions.InsertAction)
        self.assertIsInstance(insert_coins.items[0], models.Coin)

        self.assertEqual(len(insert_markets.items), 3)
        self.assertEqual(len(insert_exchange_markets.items), 3)
        self.assertIsInstance(insert_markets, actions.InsertAction)
        self.assertIsInstance(insert_exchange_markets, actions.InsertAction)
        self.assertEqual(insert_markets.items[0].buy_sym_id, "ETH")
        self.assertEqual(insert_markets.items[0].sell_sym_id, "BTC")
        self.assertEqual(insert_exchange_markets.items[0].volume, 135449.04600000)
        self.assertEqual(insert_exchange_markets.items[0].exchange_id, self.dummy_exchange.id)
        self.assertEqual(insert_markets.items[1].buy_sym_id, "LTC")
        self.assertEqual(insert_markets.items[1].sell_sym_id, "BTC")
        self.assertEqual(insert_exchange_markets.items[1].volume, 116736.71000000)
        self.assertEqual(insert_exchange_markets.items[1].exchange_id, self.dummy_exchange.id)
        self.assertEqual(insert_markets.items[2].buy_sym_id, "BNB")
        self.assertEqual(insert_markets.items[2].sell_sym_id, "BTC")
        self.assertEqual(insert_exchange_markets.items[2].volume, 3054635.71000000)
        self.assertEqual(insert_exchange_markets.items[2].exchange_id, self.dummy_exchange.id)
        
    def assertAreAllActions(self, items):
        for item in items:
            self.assertIsInstance(item, actions.Action)

    def raw_fixture(self, fixture_name):
        with open(path.join(FIXTURES_PATH, fixture_name)) as f:
            return f.read()
