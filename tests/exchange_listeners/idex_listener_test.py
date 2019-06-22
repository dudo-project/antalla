from datetime import datetime
from dateutil.parser import parse as parse_date
from decimal import Decimal
from os import path
import json
import unittest
from unittest.mock import MagicMock


from antalla import models
from antalla import actions
from antalla.exchange_listeners.idex_listener import IdexListener


FIXTURES_PATH = path.join(path.dirname(path.dirname(__file__)), "fixtures")


class IdexListenerTest(unittest.TestCase):
    def setUp(self):
        self.dummy_exchange = models.Exchange(id=1337, name="dummy")
        self.on_event_mock = MagicMock()
        self.idex_listener = IdexListener(self.dummy_exchange, self.on_event_mock)

    def test_parse_market_orders(self):
        payload = self.raw_fixture("idex/idex-order.json")
        message = dict(event="market_orders", payload=payload)
        parsed_actions = self.idex_listener._parse_message(message)
        self.assertAreAllActions(parsed_actions)
        self.assertEqual(len(parsed_actions), 2)
        insert_action = parsed_actions[0]
        self.assertIsInstance(insert_action, actions.InsertAction)
        self.assertEqual(len(insert_action.items), 1)
        order = insert_action.items[0]
        self.assertEqual(order.exchange_id, self.dummy_exchange.id)
        self.assertEqual(order.buy_sym_id, "ETH")
        self.assertEqual(order.sell_sym_id, "LTO")
        self.assertEqual(order.price, 57183587438.0/2993350626535471684.0)
        self.assertEqual(order.side, "buy")
        self.assertEqual(order.user, "0xb10de8d7571acf19f4ec5ef1cf1bc3b5369f734e")
        self.assertEqual(order.exchange_order_id,
                         "0x10c7897ade1aadd93694e14604281725acad6d3b527cb7b9031f3ea59ba213d5")
        order_size = parsed_actions[1].items[0]
        self.assertIsInstance(order_size, models.OrderSize)
        self.assertEqual(order_size.size, 2993350626535471684.0)

    def test_parse_market_cancels(self):
        raw_payload = self.raw_fixture("idex/idex-cancel.json")
        payload = json.loads(raw_payload)
        message = dict(event="market_cancels", payload=raw_payload)
        parsed_actions = self.idex_listener._parse_message(message)
        self.assertAreAllActions(parsed_actions)
        self.assertEqual(len(parsed_actions), 1)
        update_action: actions.UpdateAction = parsed_actions[0]
        self.assertIsInstance(update_action, actions.UpdateAction)
        self.assertEqual(update_action.model, models.Order)
        payload_cancel = payload["cancels"][0]
        expected_query = {
            "exchange_order_id": payload_cancel["orderHash"],
            "exchange_id": self.dummy_exchange.id,
        }
        self.assertEqual(update_action.query, expected_query)
        expected_update = {"cancelled_at": parse_date(payload_cancel["createdAt"])}
        self.assertEqual(update_action.update, expected_update)

    def test_parse_market_trades(self):
        raw_payload = self.raw_fixture("idex/idex-trade.json")
        payload = json.loads(raw_payload)
        message = dict(event="market_trades", payload=raw_payload)
        parsed_actions = self.idex_listener._parse_message(message)
        self.assertAreAllActions(parsed_actions)
        self.assertEqual(len(parsed_actions), 2)
        insert_action: actions.InsertAction = parsed_actions[0]
        self.assertIsInstance(insert_action, actions.InsertAction)
        self.assertEqual(len(insert_action.items), 1)
        self.assertIsInstance(insert_action.items[0], models.Trade)
        self.assertEqual(insert_action.items[0].exchange_order_id, payload["trades"][0]["orderHash"])

        update_action: actions.UpdateAction = parsed_actions[1]
        self.assertIsInstance(update_action, actions.UpdateAction)
        self.assertEqual(update_action.model, models.Order)
        self.assertEqual(update_action.query, {
            "exchange_order_id": payload["trades"][0]["orderHash"],
            "exchange_id": self.dummy_exchange.id,
        })
        self.assertEqual(update_action.update, {
            "filled_at": datetime.fromtimestamp(payload["trades"][0]["timestamp"]),
        })

    def test_parse_markets(self):
        payload = self.raw_fixture("idex/idex-markets.json")
        parsed_actions = self.idex_listener._parse_markets(json.loads(payload))
        self.assertAreAllActions(parsed_actions)
        self.assertEqual(len(parsed_actions), 3)
        insert_coin: actions.InsertAction = parsed_actions[0]
        insert_market: actions.InsertAction = parsed_actions[1]
        insert_market_exchange: actions.InsertAction = parsed_actions[2]
        self.assertIsInstance(insert_coin, actions.InsertAction)
        self.assertIsInstance(insert_coin.items[0], models.Coin)
        self.assertIsInstance(insert_market, actions.InsertAction)
        self.assertIsInstance(insert_market.items[0], models.Market)
        self.assertEqual(len(insert_market.items), 12)

        self.assertEqual(insert_market.items[0].first_coin_id,"LIKE")
        self.assertEqual(insert_market.items[0].second_coin_id,"WBTC")
        self.assertIsInstance(insert_market_exchange.items[0], models.ExchangeMarket)
        self.assertEqual(insert_market_exchange.items[0].exchange_id, self.dummy_exchange.id)
        self.assertEqual(insert_market_exchange.items[0].quoted_volume, 0.0)
        self.assertEqual(insert_market_exchange.items[0].quoted_volume_id, "WBTC")

        self.assertEqual(insert_market.items[1].first_coin_id,"BOUNCY")
        self.assertEqual(insert_market.items[1].second_coin_id,"ETH")
        self.assertEqual(insert_market_exchange.items[1].quoted_volume, 2.595979889336787651)
        self.assertEqual(insert_market_exchange.items[1].quoted_volume_id, "ETH")
        self.assertIsInstance(insert_market_exchange.items[1], models.ExchangeMarket)
        self.assertEqual(insert_market_exchange.items[1].exchange_id, self.dummy_exchange.id)

    def assertAreAllActions(self, items):
        for item in items:
            self.assertIsInstance(item, actions.Action)

    def raw_fixture(self, fixture_name):
        with open(path.join(FIXTURES_PATH, fixture_name)) as f:
            return f.read()
