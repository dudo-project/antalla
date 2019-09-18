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
            self.dummy_exchange = models.Exchange(id=3, name="coinbase")
            self.on_event_mock = MagicMock()
            self.session = db.Session()
            self.coinbase_listener = CoinbaseListener(self.dummy_exchange, self.on_event_mock)
            self.coinbase_listener.session = self.session
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

    def test_get_last_update_id(self):
        self._insert_data()
        dummy_db.insert_agg_order(self.session)
        self.session.flush()
        self.coinbase_listener.last_update_ids = self.coinbase_listener._get_last_update_ids()
        print(self.coinbase_listener.last_update_ids)
        self.assertEqual(self.coinbase_listener.last_update_ids["coinbaseETHBTC"], 2)


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
        # testing for inserted order: ["buy", "2", "5"]
        self.assertEqual(result[0][0], 0)
        self.assertEqual(result[0][1], "bid")
        self.assertEqual(result[0][2], "ETH")
        self.assertEqual(result[0][3], "BTC")
        self.assertEqual(result[0][4], 3)
        self.assertEqual(result[0][5], 2)
        self.assertEqual(result[0][6], 5)
        # testing for inserted order: ["buy", "2", "3"]
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
        # testing for inserted order: ["buy", "2.5", "1"]
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
        # testing for inserted order: ["sell", "6", "6"]
        self.assertEqual(result[4][0], 4)
        self.assertEqual(result[4][1], "ask")
        self.assertEqual(result[4][2], "ETH")
        self.assertEqual(result[4][3], "BTC")
        self.assertEqual(result[4][4], 3)
        self.assertEqual(result[4][5], 6)
        self.assertEqual(result[4][6], 6)
        # testing for inserted order: ["sell", "5.7", "15"]
        self.assertEqual(result[5][0], 4)
        self.assertEqual(result[5][1], "ask")
        self.assertEqual(result[5][2], "ETH")
        self.assertEqual(result[5][3], "BTC")
        self.assertEqual(result[5][4], 3)
        self.assertEqual(result[5][5], 5.7)
        self.assertEqual(result[5][6], 15)
        # testing for inserted order: ["buy", "3", "0.5"]
        self.assertEqual(result[6][0], 4)
        self.assertEqual(result[6][1], "bid")
        self.assertEqual(result[6][2], "ETH")
        self.assertEqual(result[6][3], "BTC")
        self.assertEqual(result[6][4], 3)
        self.assertEqual(result[6][5], 3)
        self.assertEqual(result[6][6], 0.5)
        # testing for correct return result of current order book state
        current_order_book = self.session.execute(
            """
            with latest_orders as (
                      select order_type, price, max(last_update_id) max_update_id, exchange_id
                      from aggregate_orders
                      group by aggregate_orders.price, aggregate_orders.order_type, aggregate_orders.exchange_id)
                  select order_type,
                         price,
                         size,
                         last_update_id,
                         timestamp,
                         ex.name,
                         buy_sym_id,
                         sell_sym_id
                  from aggregate_orders
                           inner join exchanges ex on aggregate_orders.exchange_id = ex.id
                  where (order_type, price, last_update_id, exchange_id) in (select * from latest_orders)
                    and size > 0
                    and buy_sym_id = 'ETH'
                    and sell_sym_id = 'BTC'
                    and ex.name = 'coinbase'
                  order by price asc
            """
        )
        all_orders = []
        for order in list(current_order_book):
            all_orders.append(dict(
                order_type=order[0],
                price=order[1],
                size=order[2],
                timestamp=order[4],
                last_update_id=order[3],
                exchange=order[5]
            ))
        # testing if correct orders are being returned (none with size 0)
        self.assertEqual(len(all_orders), 5)
        self.assertEqual(all_orders[0]["size"], 3)
        self.assertEqual(all_orders[0]["last_update_id"], 1)
        self.assertEqual(all_orders[0]["price"], 2)
        
        self.assertEqual(all_orders[1]["size"], 1)
        self.assertEqual(all_orders[1]["last_update_id"], 2)
        self.assertEqual(all_orders[1]["price"], 2.5)
        
        self.assertEqual(all_orders[2]["size"], 0.5)
        self.assertEqual(all_orders[2]["last_update_id"], 4)
        self.assertEqual(all_orders[2]["price"], 3)
        
        self.assertEqual(all_orders[3]["size"], 15)
        self.assertEqual(all_orders[3]["last_update_id"], 4)
        self.assertEqual(all_orders[3]["price"], 5.7)
        
        self.assertEqual(all_orders[4]["size"], 6)
        self.assertEqual(all_orders[4]["last_update_id"], 4)
        self.assertEqual(all_orders[4]["price"], 6)
        self.assertEqual(all_orders[4]["exchange"], self.dummy_exchange.name)

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

    def test_parse_message(self):
        message = dict(type="activate")
        response = self.coinbase_listener._parse_message(message)
        self.assertEqual(response, [])

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