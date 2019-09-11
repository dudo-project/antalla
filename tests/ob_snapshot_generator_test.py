import unittest

from antalla import ob_snapshot_generator

class ModelsTest(unittest.TestCase):
    def test_compute_stats(self):
        order_book = [{"order_type":"bid", "price": 0.5, "size": 10}, {"order_type":"ask", "price": 1.1, "size": 5},\
        {"order_type":"bid", "price": 0.75, "size": 30}, {"order_type":"bid", "price": 0.8, "size": 5},\
        {"order_type":"ask", "price": 1.08, "size": 4}, {"order_type":"ask", "price": 1.02, "size": 7},\
        {"order_type":"bid", "price": 0.95, "size": 7}, {"order_type":"ask", "price": 0.97, "size": 3}]
        generator = ob_snapshot_generator.OBSnapshotGenerator('hitbtc', 0)
        output = generator._compute_stats(order_book)
        self.assertEqual(output["spread"], 0.020000000000000018)
        self.assertEqual(output["min_ask_price"], 0.97)
        self.assertEqual(output["min_ask_size"], 3)
        self.assertEqual(output["max_bid_price"], 0.95)
        self.assertEqual(output["max_bid_size"], 7)
        self.assertEqual(output["bids_volume"], 38.15)
        self.assertEqual(output["asks_volume"], 19.87 )
        self.assertEqual(output["bids_count"], 4)
        self.assertEqual(output["asks_count"], 4)
        self.assertEqual(output["bids_price_stddev"], 0.1620185174601965)
        self.assertEqual(output["asks_price_stddev"], 0.05117372372614685)
        self.assertEqual(output["bids_price_mean"], 0.75)
        self.assertEqual(output["asks_price_mean"], 1.0425)
        self.assertEqual(output["bid_price_median"], 0.775)
        self.assertEqual(output["ask_price_median"], 1.05)
        self.assertEqual(output["bid_price_upper_quartile"], 0.5)
        self.assertEqual(output["ask_price_lower_quartile"], 1.1)
        