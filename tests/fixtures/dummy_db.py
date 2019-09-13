from antalla import db
from antalla import models
import datetime

def insert_exchanges(session):
    session.add_all([
        models.Exchange(
            name='hitbtc',
            id=1
        ),
        models.Exchange(
            name='binance',
            id=2
        )
    ])

def insert_coins(session):
    session.add_all([
        models.Coin(
            symbol='BTC',
            name="bitcoin"
        ),
        models.Coin(
            symbol='ETH',
            name='ether'
        )
    ])

def insert_agg_order(session):
    session.add_all([
        models.AggOrder(
            last_update_id=1,
            timestamp=datetime.datetime(2019, 5, 15, 19, 30, 0, 363064),
            buy_sym_id='ETH',
            sell_sym_id='BTC',
            exchange_id=1,
            order_type='bid',
            price=0.5,
            size=10,
        ),
        models.AggOrder(
            last_update_id=1,
            timestamp=datetime.datetime(2019, 5, 15, 19, 30, 0, 363064),
            buy_sym_id='ETH',
            sell_sym_id='BTC',
            exchange_id=1,
            order_type='ask',
            price=0.6,
            size=6,
        ),
        models.AggOrder(
            last_update_id=2,
            timestamp=datetime.datetime(2019, 5, 15, 19, 31, 30, 372835),
            buy_sym_id='ETH',
            sell_sym_id='BTC',
            exchange_id=1,
            order_type='bid',
            price=0.3,
            size=12,
        ),
        models.AggOrder(
            last_update_id=2,
            timestamp=datetime.datetime(2019, 5, 15, 19, 31, 30, 372835),
            buy_sym_id='ETH',
            sell_sym_id='BTC',
            exchange_id=1,
            order_type='ask',
            price=0.7,
            size=2,
        ),
        models.AggOrder(
            last_update_id=2,
            timestamp=datetime.datetime(2019, 5, 15, 19, 31, 30, 372835),
            buy_sym_id='ETH',
            sell_sym_id='BTC',
            exchange_id=1,
            order_type='ask',
            price=0.65,
            size=6,
        ),
        models.AggOrder(
            last_update_id=3,
            timestamp=datetime.datetime(2019, 5, 15, 19, 32, 45, 0),
            buy_sym_id='ETH',
            sell_sym_id='BTC',
            exchange_id=1,
            order_type='bid',
            price=0.1,
            size=10,
        ),
        models.AggOrder(
            last_update_id=3,
            timestamp=datetime.datetime(2019, 5, 15, 19, 32, 45, 0),
            buy_sym_id='ETH',
            sell_sym_id='BTC',
            exchange_id=1,
            order_type='bid',
            price=0.4,
            size=6,
        ),
        models.AggOrder(
            last_update_id=4,
            timestamp=datetime.datetime(2019, 5, 15, 19, 33, 25, 0),
            buy_sym_id='ETH',
            sell_sym_id='BTC',
            exchange_id=1,
            order_type='bid',
            price=0.1,
            size=0,
        ),
        models.AggOrder(
            last_update_id=5,
            timestamp=datetime.datetime(2019, 5, 15, 19, 34, 8, 0),
            buy_sym_id='BTC',
            sell_sym_id='ETH',
            exchange_id=1,
            order_type='bid',
            price=0.3,
            size=6,
        ),
        models.AggOrder(
            last_update_id=5,
            timestamp=datetime.datetime(2019, 5, 15, 19, 34, 8, 0),
            buy_sym_id='ETH',
            sell_sym_id='BTC',
            exchange_id=1,
            order_type='ask',
            price=0.6,
            size=3,
        ),
        models.AggOrder(
            last_update_id=5,
            timestamp=datetime.datetime(2019, 5, 15, 19, 34, 8, 0),
            buy_sym_id='ETH',
            sell_sym_id='BTC',
            exchange_id=1,
            order_type='bid',
            price=0.5,
            size=4,
        ),
        models.AggOrder(
            last_update_id=6,
            timestamp=datetime.datetime(2019, 5, 15, 19, 35, 56, 0),
            buy_sym_id='ETH',
            sell_sym_id='BTC',
            exchange_id=1,
            order_type='ask',
            price=0.65,
            size=6,
        ),
        models.AggOrder(
            last_update_id=1,
            timestamp=datetime.datetime(2019, 5, 15, 19, 32, 32, 423422),
            buy_sym_id='ETH',
            sell_sym_id='BTC',
            exchange_id=2,
            order_type='ask',
            price=0.5,
            size=10,
        ),
        models.AggOrder(
            last_update_id=1,
            timestamp=datetime.datetime(2019, 5, 15, 19, 32, 32, 423422),
            buy_sym_id='ETH',
            sell_sym_id='BTC',
            exchange_id=2,
            order_type='bid',
            price=0.4,
            size=5,
        ),
        models.AggOrder(
            last_update_id=2,
            timestamp=datetime.datetime(2019, 5, 15, 19, 33, 23, 123456),
            buy_sym_id='ETH',
            sell_sym_id='BTC',
            exchange_id=2,
            order_type='bid',
            price=0.35,
            size=7,
        ),
        models.AggOrder(
            last_update_id=2,
            timestamp=datetime.datetime(2019, 5, 15, 19, 33, 23, 123456),
            buy_sym_id='ETH',
            sell_sym_id='BTC',
            exchange_id=2,
            order_type='ask',
            price=0.6,
            size=4,
        ) 
    ])

def insert_exchange_markets(session):
    session.add_all([
        models.ExchangeMarket(
            quoted_volume=123456,
            first_coin_id='BTC',
            second_coin_id='ETH',
            exchange_id=1,
            quoted_volume_id='ETH',
            original_name='ETHBTC'
        )
    ])

def insert_markets(session):
    session.add_all([
        models.Market(
            first_coin_id='BTC',
            second_coin_id='ETH'
        )
    ])

def insert_events(session):
    session.add_all([
        models.Event(
            session_id='test-001',
            timestamp=datetime.datetime(2019, 5, 15, 19, 30, 0, 0),
            connection_event='connect',
            data_collected='agg_order_book',
            buy_sym_id='ETH',
            sell_sym_id='BTC',
            exchange_id=1
        ),
        models.Event(
            session_id='test-001',
            timestamp=datetime.datetime(2019, 5, 15, 19, 35, 45, 0),
            connection_event='disconnect',
            data_collected='agg_order_book',
            buy_sym_id='ETH',
            sell_sym_id='BTC',
            exchange_id=1
        ),
        models.Event(
            session_id='test-002',
            timestamp=datetime.datetime(2019, 5, 15, 19, 34, 30, 0),
            connection_event='connect',
            data_collected='agg_order_book',
            buy_sym_id='ETH',
            sell_sym_id='BTC',
            exchange_id=2
        ),
        models.Event(
            session_id='test-002',
            timestamp=datetime.datetime(2019, 5, 15, 19, 38, 34, 0),
            connection_event='disconnect',
            data_collected='agg_order_book',
            buy_sym_id='ETH',
            sell_sym_id='BTC',
            exchange_id=2
        ),
        models.Event(
            session_id='test-001',
            timestamp=datetime.datetime(2019, 5, 15, 19, 36, 0, 0),
            connection_event='connect',
            data_collected='agg_order_book',
            buy_sym_id='ETH',
            sell_sym_id='BTC',
            exchange_id=1
        ),
        models.Event(
            session_id='test-001',
            timestamp=datetime.datetime(2019, 5, 15, 19, 38, 0, 0),
            connection_event='disconnect',
            data_collected='agg_order_book',
            buy_sym_id='ETH',
            sell_sym_id='BTC',
            exchange_id=1
        ),
        models.Event(
            session_id='test-001',
            timestamp=datetime.datetime(2019, 5, 15, 19, 39, 0, 0),
            connection_event='connect',
            data_collected='agg_order_book',
            buy_sym_id='ETH',
            sell_sym_id='BTC',
            exchange_id=1
        )
    ])

def insert_snapshot(session):
    session.add_all([
        models.OrderBookSnapshot(
            timestamp=datetime.datetime(2019, 5, 15, 19, 37, 0, 0), 
            buy_sym_id='ETH',
            sell_sym_id='BTC',
            exchange_id=1,
            spread=0.25,
            bids_volume=15.0,
            asks_volume=25.75,
            bids_count=200,
            asks_count=150,
            bids_price_stddev=0.5,
            asks_price_stddev=0.6,
            bids_price_mean=5,
            asks_price_mean=7,
            min_ask_price=6.1,
            min_ask_size=7,
            max_bid_price=5.9,
            max_bid_size=10,
            bid_price_median=4.8,
            ask_price_median=7.2,
            bid_price_upper_quartile=4.7,
            ask_price_lower_quartile=8.2,
            bids_volume_upper_quartile=9,
            asks_volume_lower_quartile=14,
            bids_count_upper_quartile=100,
            asks_count_lower_quartile=75,
            bids_price_stddev_upper_quartile=0.3,
            asks_price_stddev_lower_quartile=0.2,
            bids_price_mean_upper_quartile= 5.5,
            asks_price_mean_lower_quartile=6.8 
        )
    ])