import unittest
import hashlib
from datetime import datetime

from antalla import models


class ModelsTest(unittest.TestCase):
    def test_coin_repr(self):
        coin = models.Coin(symbol="ETH")
        self.assertEqual(str(coin), "Coin(symbol='ETH')")

    def test_exchange_repr(self):
        exchange = models.Exchange(name="idex")
        self.assertEqual(str(exchange), "Exchange(name='idex')")

    def test_order_repr(self):
        order = models.Order(exchange_id=1, exchange_order_id="abc")
        expected= "Order(exchange_id=1, exchange_order_id='abc')"
        self.assertEqual(str(order), expected)

    def test_market_order_funds_repr(self):
        market_order_fund = models.MarketOrderFunds(id=1)
        self.assertEqual(str(market_order_fund), "MarketOrderFunds(id=1)")

    def test_order_size_repr(self):
        order_size = models.OrderSize(id=1)
        self.assertEqual(str(order_size), "OrderSize(id=1)")

    def test_trade_repr(self):
        trade = models.Trade(exchange_trade_id=1)
        self.assertEqual(str(trade), "Trade(id=1)")

    #def test_agg_order_repr(self):