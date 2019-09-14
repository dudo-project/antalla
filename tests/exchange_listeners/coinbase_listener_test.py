from datetime import datetime
from dateutil.parser import parse as parse_date
from decimal import Decimal
from os import path
import json
import unittest
from unittest.mock import MagicMock

from tests.fixtures import dummy_db
from antalla import models
from antalla import actions
from antalla import db
from antalla.exchange_listeners.coinbase_listener import CoinbaseListener

FIXTURES_PATH = path.join(path.dirname(path.dirname(__file__)), "fixtures")

class CoinbaseListenerTest(unittest.TestCase):
    def setUp(self):
            self.dummy_exchange = models.Exchange(id=3, name="dummy")
            self.on_event_mock = MagicMock()
            self.coinbase_listener = CoinbaseListener(self.dummy_exchange, self.on_event_mock)
            self.session = db.Session()
            self.session.commit = lambda: None

    def tearDown(self):
        self.session.rollback()

    def _insert_data(self):
        dummy_db.insert_coins(self.session)
        dummy_db.insert_exchange_markets(self.session)
        dummy_db.insert_exchanges(self.session)
        dummy_db.insert_markets(self.session)
        self.session.flush()

    def assertAreAllActions(self, items):
        for item in items:
            self.assertIsInstance(item, actions.Action)

    def raw_fixture(self, fixture_name):
        with open(path.join(FIXTURES_PATH, fixture_name)) as f:
            return f.read()

    def test_parse_l2update_transaction(self):
        self._insert_data()
        update_1 = {
            "type": "l2update",
            "product_id": "ETH-BTC",
            "changes": [
                ["buy", "2", "5"]
            ]   
        }
        actions = self.coinbase_listener._parse_l2update(update_1)
        for a in actions:
            a.execute(self.session)
        self.session.flush()
        resultproxy = self.session.execute("select count(*) from aggregate_orders")
        result = list(resultproxy)
        self.assertTrue(len(result) > 0)
        self.assertEqual(result[0][0], 1)
        update_2 = {
            "type": "l2update",
            "product_id": "ETH-BTC",
            "changes": [
                ["buy", "2", "3"]
            ]   
        }
        actions = self.coinbase_listener._parse_l2update(update_2)
        for a in actions:
            a.execute(self.session)
        self.session.flush()
        resultproxy = self.session.execute("select last_update_id, order_type, buy_sym_id, sell_sym_id, exchange_id, price, size from aggregate_orders order by last_update_id asc")
        result = list(resultproxy)
        self.assertTrue(len(result) > 0)
        self.assertEqual(result[0][0], 0)
        self.assertEqual(result[0][1], "bid")
        self.assertEqual(result[0][2], "ETH")
        self.assertEqual(result[0][3], "BTC")
        self.assertEqual(result[0][4], 3)
        self.assertEqual(result[0][5], 2)
        self.assertEqual(result[0][6], 5)

        self.assertEqual(result[1][0], 1)
        self.assertEqual(result[1][1], "bid")
        self.assertEqual(result[1][2], "ETH")
        self.assertEqual(result[1][3], "BTC")
        self.assertEqual(result[1][4], 3)
        self.assertEqual(result[1][5], 2)
        self.assertEqual(result[1][6], 3)
        update_3 = {
            "type": "l2update",
            "product_id": "ETH-BTC",
            "changes": [
                ["buy", "2.5", "1"]
            ]   
        }
        actions = self.coinbase_listener._parse_l2update(update_3)
        for a in actions:
            a.execute(self.session)
        self.session.flush()
        resultproxy = self.session.execute("select last_update_id, order_type, buy_sym_id, sell_sym_id, exchange_id, price, size from aggregate_orders order by last_update_id asc")
        result = list(resultproxy)
        self.assertEqual(result[2][0], 2)
        self.assertEqual(result[2][1], "bid")
        self.assertEqual(result[2][2], "ETH")
        self.assertEqual(result[2][3], "BTC")
        self.assertEqual(result[2][4], 3)
        self.assertEqual(result[2][5], 2.5)
        self.assertEqual(result[2][6], 1)
        update_4 = {
            "type": "l2update",
            "product_id": "ETH-BTC",
            "changes": [
                ["sell", "6", "10"]
            ]   
        }
        actions = self.coinbase_listener._parse_l2update(update_4)
        for a in actions:
            a.execute(self.session)
        self.session.flush()
        resultproxy = self.session.execute("select last_update_id, order_type, buy_sym_id, sell_sym_id, exchange_id, price, size from aggregate_orders order by last_update_id asc")
        result = list(resultproxy)
        self.assertEqual(result[3][0], 3)
        self.assertEqual(result[3][1], "ask")
        self.assertEqual(result[3][2], "ETH")
        self.assertEqual(result[3][3], "BTC")
        self.assertEqual(result[3][4], 3)
        self.assertEqual(result[3][5], 6)
        self.assertEqual(result[3][6], 10)
        update_5 = {
            "type": "l2update",
            "product_id": "ETH-BTC",
            "changes": [
                ["sell", "6", "6"],
                ["buy", "3", "0.5"],
                ["sell", "5.7", "15"]
            ]   
        }
        actions = self.coinbase_listener._parse_l2update(update_5)
        for a in actions:
            a.execute(self.session)
        self.session.flush()
        resultproxy = self.session.execute("select last_update_id, order_type, buy_sym_id, sell_sym_id, exchange_id, price, size from aggregate_orders order by last_update_id asc, price desc")
        result = list(resultproxy)
        self.assertEqual(len(result), 7)
        self.assertEqual(result[4][0], 4)
        self.assertEqual(result[4][1], "ask")
        self.assertEqual(result[4][2], "ETH")
        self.assertEqual(result[4][3], "BTC")
        self.assertEqual(result[4][4], 3)
        self.assertEqual(result[4][5], 6)
        self.assertEqual(result[4][6], 6)

        self.assertEqual(result[5][0], 4)
        self.assertEqual(result[5][1], "ask")
        self.assertEqual(result[5][2], "ETH")
        self.assertEqual(result[5][3], "BTC")
        self.assertEqual(result[5][4], 3)
        self.assertEqual(result[5][5], 5.7)
        self.assertEqual(result[5][6], 15)

        self.assertEqual(result[6][0], 4)
        self.assertEqual(result[6][1], "bid")
        self.assertEqual(result[6][2], "ETH")
        self.assertEqual(result[6][3], "BTC")
        self.assertEqual(result[6][4], 3)
        self.assertEqual(result[6][5], 3)
        self.assertEqual(result[6][6], 0.5)


    def test_parse_snapshot(self):
        payload = self.raw_fixture("coinbase/coinbase-snapshot.json")
        parsed_actions = self.coinbase_listener._parse_snapshot(json.loads(payload))
        self.assertAreAllActions(parsed_actions)
        self.assertEqual(len(parsed_actions), 1)
        insert_action = parsed_actions[0]
        self.assertIsInstance(insert_action, actions.InsertAction)
        self.assertEqual(len(insert_action.items), 6)
        agg_order = insert_action.items[0]
        self.assertEqual(agg_order.exchange_id, self.dummy_exchange.id)
        self.assertEqual(agg_order.order_type, "bid")
        self.assertEqual(agg_order.buy_sym_id, "BTC")
        self.assertEqual(agg_order.sell_sym_id, "EUR")
        self.assertEqual(agg_order.price, 0.5)
        self.assertEqual(agg_order.size, 10.0)
        agg_order = insert_action.items[3]
        self.assertEqual(agg_order.exchange_id, self.dummy_exchange.id)
        self.assertEqual(agg_order.order_type, "ask")
        self.assertEqual(agg_order.buy_sym_id, "BTC")
        self.assertEqual(agg_order.sell_sym_id, "EUR")
        self.assertEqual(agg_order.price, 2.0)
        self.assertEqual(agg_order.size, 20.0)

    def test_parse_l2update(self):
        payload = self.raw_fixture("coinbase/coinbase-l2update.json")
        parsed_actions = self.coinbase_listener._parse_l2update(json.loads(payload))
        self.assertAreAllActions(parsed_actions)
        self.assertEqual(len(parsed_actions), 1)
        insert_action = parsed_actions[0]
        self.assertIsInstance(insert_action, actions.InsertAction)
        self.assertEqual(len(insert_action.items), 4)
        agg_order = insert_action.items[0]
        self.assertEqual(agg_order.exchange_id, self.dummy_exchange.id)
        self.assertEqual(agg_order.order_type, "bid")
        self.assertEqual(agg_order.buy_sym_id, "BTC")
        self.assertEqual(agg_order.sell_sym_id, "EUR")
        self.assertEqual(agg_order.price, 0.75)
        self.assertEqual(agg_order.size, 6.0)
        self.assertEqual(agg_order.last_update_id, 0)
        agg_order = insert_action.items[3]
        self.assertEqual(agg_order.exchange_id, self.dummy_exchange.id)
        self.assertEqual(agg_order.order_type, "ask")
        self.assertEqual(agg_order.buy_sym_id, "BTC")
        self.assertEqual(agg_order.sell_sym_id, "EUR")
        self.assertEqual(agg_order.price, 0.95)
        self.assertEqual(agg_order.size, 20.0)
        self.assertEqual(agg_order.last_update_id, 0)
        
    def test_parse_open(self):
        payload = self.raw_fixture("coinbase/coinbase-open.json")
        parsed_actions = self.coinbase_listener._parse_open(json.loads(payload))
        self.assertAreAllActions(parsed_actions)
        self.assertEqual(len(parsed_actions), 2)
        insert_action = parsed_actions[0]
        self.assertIsInstance(insert_action, actions.InsertAction)
        self.assertEqual(len(insert_action.items), 1)
        order = insert_action.items[0]
        self.assertEqual(order.exchange_id, self.dummy_exchange.id)
        self.assertEqual(order.buy_sym_id, "BTC")
        self.assertEqual(order.sell_sym_id, "USD")
        self.assertEqual(order.exchange_order_id, "d50ec984-77a8-460a-b958-66f114b0de9b")
        self.assertEqual(order.price, 200.2)
        self.assertEqual(order.side, "sell")
        order_size = parsed_actions[1].items[0]
        self.assertIsInstance(order_size, models.OrderSize)
        self.assertEqual(order_size.size, 1.0)

    def test_parse_done_filled(self):
        payload = self.raw_fixture("coinbase/coinbase-done-filled.json")
        parsed_actions = self.coinbase_listener._parse_done(json.loads(payload))
        self.assertAreAllActions(parsed_actions)
        self.assertEqual(len(parsed_actions), 1)
        update_action = parsed_actions[0]
        self.assertIsInstance(update_action, actions.UpdateAction)
        
    def test_parse_change(self):
        payload = self.raw_fixture("coinbase/coinbase-change.json")
        parsed_actions = self.coinbase_listener._parse_change(json.loads(payload))
        self.assertAreAllActions(parsed_actions)
        self.assertEqual(len(parsed_actions), 1)
        insert_action = parsed_actions[0]
        order_size = insert_action.items[0]
        self.assertIsInstance(insert_action, actions.InsertAction)
        self.assertEqual(order_size.size, 5.23512)
        self.assertEqual(order_size.timestamp, parse_date("2014-11-07T08:19:27.028459Z"))
        self.assertEqual(order_size.exchange_order_id, "ac928c66-ca53-498f-9c13-a110027a60e8")

    def test_parse_received_funds(self):
        payload = self.raw_fixture("coinbase/coinbase-received-funds.json")
        parsed_actions = self.coinbase_listener._parse_received(json.loads(payload))
        self.assertAreAllActions(parsed_actions)
        self.assertEqual(len(parsed_actions), 2)
        insert_action = parsed_actions[0]
        self.assertIsInstance(insert_action, actions.InsertAction)
        self.assertEqual(len(insert_action.items), 1)
        order = insert_action.items[0]
        self.assertEqual(order.exchange_id, self.dummy_exchange.id)
        self.assertEqual(order.side, "buy")
        self.assertEqual(order.order_type, "market")
        self.assertEqual(order.exchange_order_id, "dddec984-77a8-460a-b958-66f114b0de9b")
        self.assertEqual(order.timestamp, parse_date("2014-11-09T08:19:27.028459Z"))
        self.assertEqual(order.buy_sym_id, "BTC")
        self.assertEqual(order.sell_sym_id, "USD")

        order_funds = parsed_actions[1].items[0]
        self.assertIsInstance(order_funds, models.MarketOrderFunds)
        self.assertEqual(order_funds.funds, 3000.234)

    def test_parse_message(self):
        message = dict(type="activate")
        response = self.coinbase_listener._parse_message(message)
        self.assertEqual(response, [])

    def test_parse_received(self):
        payload = self.raw_fixture("coinbase/coinbase-received.json")
        parsed_actions = self.coinbase_listener._parse_received(json.loads(payload))
        self.assertAreAllActions(parsed_actions)
        self.assertEqual(len(parsed_actions), 2)
        insert_action = parsed_actions[0]
        self.assertIsInstance(insert_action, actions.InsertAction)
        self.assertEqual(len(insert_action.items), 1)
        order = insert_action.items[0]
        self.assertEqual(order.exchange_id, self.dummy_exchange.id)
        self.assertEqual(order.buy_sym_id, "BNB")
        self.assertEqual(order.sell_sym_id, "BTC")
        self.assertEqual(order.exchange_order_id, "d50ec984-77a8-460a-b958-66f114b0de9b")
        self.assertEqual(order.price, 502.1)
        self.assertEqual(order.side, "buy")
        self.assertEqual(order.timestamp, parse_date("2014-11-07T08:19:27.028459Z"))

        order_size = parsed_actions[1].items[0]
        self.assertIsInstance(order_size, models.OrderSize)
        self.assertEqual(order_size.size, 1.34)

    def test_parse_match(self):
        payload = self.raw_fixture("coinbase/coinbase-match.json")
        parsed_actions = self.coinbase_listener._parse_match(json.loads(payload))
        self.assertAreAllActions(parsed_actions)
        self.assertEqual(len(parsed_actions), 1)
        insert_action = parsed_actions[0]
        self.assertIsInstance(insert_action, actions.InsertAction)
        self.assertEqual(len(insert_action.items), 1)
        order = insert_action.items[0]
        self.assertEqual(order.exchange_id, self.dummy_exchange.id)
        self.assertEqual(order.buy_sym_id, "BTC")
        self.assertEqual(order.sell_sym_id, "BNB")
        self.assertEqual(order.price, 400.23)
        self.assertEqual(order.size, 5.23512)
        self.assertEqual(order.timestamp, parse_date("2014-11-07T08:19:27.028459Z"))
        #self.assertEqual(order.maker_order_id, "ac928c66-ca53-498f-9c13-a110027a60e8")
        #self.assertEqual(order.taker_order_id, "132fb6ae-456b-4654-b4e0-d681ac05cea1")

    def test_parse_markets(self):
        raw_markets = self.raw_fixture("coinbase/coinbase-markets.json")
        markets = self.coinbase_listener._parse_market(json.loads(raw_markets))
        ticker = json.loads(self.raw_fixture("coinbase/coinbase-volume.json"))
        insert_actions_markets = []
        insert_actions_exchange_markets = []
        for market in markets:
            all_markets = [self.coinbase_listener._parse_volume(ticker, market)]
            parsed_actions = self.coinbase_listener._parse_markets(all_markets)
            self.assertEqual(len(parsed_actions), 3)
            self.assertIsInstance(parsed_actions[0].items[0], models.Coin)
            insert_actions_markets.append(parsed_actions[1])
            insert_actions_exchange_markets.append(parsed_actions[2])
        self.assertEqual(insert_actions_markets[0].items[0].first_coin_id, "REP")
        self.assertEqual(insert_actions_markets[0].items[0].second_coin_id, "USD")
        self.assertEqual(insert_actions_exchange_markets[0].items[0].quoted_volume_id, "REP")
        self.assertEqual(insert_actions_exchange_markets[0].items[0].quoted_volume, 60486.28451826)
        self.assertEqual(insert_actions_exchange_markets[0].items[0].exchange_id, self.dummy_exchange.id)

    def test_parse_done_cancel(self):
        payload = self.raw_fixture("coinbase/coinbase-done-canceled.json")
        parsed_actions = self.coinbase_listener._parse_done(json.loads(payload))
        self.assertAreAllActions(parsed_actions)
        self.assertEqual(len(parsed_actions), 1)
        update_action = parsed_actions[0]
        self.assertIsInstance(update_action, actions.UpdateAction)
        
