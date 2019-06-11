from decimal import Decimal
from os import path
import unittest
from unittest.mock import MagicMock


from antalla import models
from antalla.actions import Action
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
        actions = self.idex_listener._parse_message(message)
        self.assertAreAllActions(actions)
        self.assertEqual(len(actions), 1)
        insert_action = actions[0]
        self.assertEqual(len(insert_action.items), 1)
        order = insert_action.items[0]
        self.assertEqual(order.exchange, self.dummy_exchange)
        self.assertEqual(order.buy_sym_id, "ETH")
        self.assertEqual(order.sell_sym_id, "LTO")
        self.assertEqual(order.amount_buy, 2993350626535471684.0)
        self.assertEqual(order.amount_sell, 57183587438.0)
        self.assertEqual(order.user, "0xb10de8d7571acf19f4ec5ef1cf1bc3b5369f734e")
        self.assertEqual(order.exchange_order_id,
                         "0x10c7897ade1aadd93694e14604281725acad6d3b527cb7b9031f3ea59ba213d5")

    def assertAreAllActions(self, items):
        for item in items:
            self.assertIsInstance(item, Action)

    def raw_fixture(self, fixture_name):
        with open(path.join(FIXTURES_PATH, fixture_name)) as f:
            return f.read()
