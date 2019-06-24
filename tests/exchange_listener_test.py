import unittest
from unittest.mock import MagicMock

from antalla import models
from antalla.exchange_listener import ExchangeListener


class DummyListener(ExchangeListener):
    def _find_market(self, market):
        if market == "ETH_BTC":
            return models.ExchangeMarket(
                original_name="ETH_BTC"
            )
        return False


class ExchangeListenerTest(unittest.TestCase):
    def setUp(self):
        self.exchange = models.Exchange(name="foo")
        self.on_event = MagicMock()

    def test_initalization(self):
        markets = ["ETH_BTC", "BTC_LTC"]
        listener = DummyListener(self.exchange, self.on_event, markets)
        self.assertEqual(listener.markets, ["ETH_BTC"])
